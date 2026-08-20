"""Google Analytics 4 Data API client (plain HTTP via httpx).

Rule 3: this layer only talks to Google — parsing/normalizing belongs to the
module. Read-only access; never writes anything to the GA property.
"""
import httpx

from app.core.http import http_client

from app.core.exceptions import UpstreamError

TIMEOUT = 30.0
DATA_API = "https://analyticsdata.googleapis.com/v1beta"
ADMIN_API = "https://analyticsadmin.googleapis.com/v1"


class GoogleAnalyticsClient:
    def __init__(self, access_token: str):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def list_properties(self) -> list[dict]:
        """Account summaries -> flat [{property_id, property_name, account_name}]."""
        async with http_client(timeout=TIMEOUT, headers=self.headers) as client:
            response = await client.get(f"{ADMIN_API}/accountSummaries", params={"pageSize": 100})
        self._check(response)
        summaries = response.json().get("accountSummaries", [])
        flat: list[dict] = []
        for account in summaries:
            for prop in account.get("propertySummaries", []):
                flat.append({
                    "property_id": prop.get("property", "").replace("properties/", ""),
                    "property_name": prop.get("displayName"),
                    "account_name": account.get("displayName"),
                })
        return flat

    async def run_daily_report(self, property_id: str, days: int = 28) -> dict:
        """Sessions / active users / pageviews per day for the trailing window."""
        body = {
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "yesterday"}],
            "dimensions": [{"name": "date"}],
            "metrics": [{"name": "sessions"}, {"name": "activeUsers"}, {"name": "screenPageViews"}],
            "orderBys": [{"dimension": {"dimensionName": "date"}, "asc": True}],
        }
        async with http_client(timeout=TIMEOUT, headers=self.headers) as client:
            response = await client.post(f"{DATA_API}/properties/{property_id}:runReport", json=body)
        self._check(response)
        return response.json()

    def _check(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                details = response.json()
            except ValueError:
                details = {"body": response.text[:300]}
            details["status_code"] = response.status_code
            raise UpstreamError(
                "ga.api_error",
                f"Google Analytics API returned {response.status_code}",
                details=details,
            )

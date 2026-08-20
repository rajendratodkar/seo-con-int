"""Search Console REST API client (Rule 3: API integration only, no analysis here)."""
import httpx

from app.core.http import http_client

from app.core.exceptions import UpstreamError

API_ROOT = "https://searchconsole.googleapis.com/webmasters/v3"


class SearchConsoleClient:
    def __init__(self, access_token: str):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def list_sites(self) -> list[dict]:
        async with http_client(timeout=30.0, headers=self.headers) as client:
            response = await client.get(f"{API_ROOT}/sites")
        if response.status_code != 200:
            raise UpstreamError("search_console.api_error", "Failed to list properties", details=response.json())
        return response.json().get("siteEntry", [])

    async def query_report(
        self,
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions: list[str],
        row_limit: int = 25000,
        start_row: int = 0,
    ) -> dict:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "startRow": start_row,
        }
        async with http_client(timeout=60.0, headers=self.headers) as client:
            response = await client.post(f"{API_ROOT}/sites/{site_url}/searchAnalytics/query", json=body)
        if response.status_code != 200:
            raise UpstreamError("search_console.api_error", "Report query failed", details=response.json())
        return response.json()

"""WordPress REST API v2 client (plain HTTP via httpx).

Authentication uses Application Passwords (HTTP Basic). Business logic never
lives here — this layer only talks to WordPress and raises UpstreamError on failure.
"""
import httpx

from app.core.http import http_client

from app.core.exceptions import UpstreamError

TIMEOUT = 30.0


class WordPressClient:
    def __init__(self, site_url: str, user: str, app_password: str):
        self.base = site_url.rstrip("/") + "/wp-json/wp/v2"
        self.auth = (user, app_password)

    async def test_connection(self) -> dict:
        async with http_client(timeout=TIMEOUT, auth=self.auth) as client:
            response = await client.get(f"{self.base}/users/me")
        self._check(response)
        data = response.json()
        return {"name": data.get("name"), "slug": data.get("slug")}

    async def create_post(self, title: str, html: str, status: str = "draft") -> dict:
        """status: draft | publish. Returns the created post (id, link, status)."""
        async with http_client(timeout=TIMEOUT, auth=self.auth) as client:
            response = await client.post(
                f"{self.base}/posts",
                json={"title": title, "content": html, "status": status},
            )
        self._check(response)
        return response.json()

    async def update_post(self, post_id: int, fields: dict) -> dict:
        async with http_client(timeout=TIMEOUT, auth=self.auth) as client:
            response = await client.post(f"{self.base}/posts/{post_id}", json=fields)
        self._check(response)
        return response.json()

    def _check(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                details = response.json()
            except ValueError:
                details = {"body": response.text[:300]}
            raise UpstreamError(
                "wordpress.api_error",
                f"WordPress API returned {response.status_code}",
                details=details,
            )

"""GitHub Contents API client for Astro/static-site publishing (plain HTTP via httpx).

Flow: read file (get sha if it exists) -> create-or-update file -> commit on a branch.
Business logic never lives here — raises UpstreamError on failure.
"""
import base64

import httpx

from app.core.http import http_client

from app.core.exceptions import UpstreamError

TIMEOUT = 30.0
API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }

    async def get_file_sha(self, repo: str, path: str, branch: str) -> str | None:
        """Returns the blob sha if the file exists, else None (needed for updates)."""
        async with http_client(timeout=TIMEOUT, headers=self.headers) as client:
            response = await client.get(f"{API}/repos/{repo}/contents/{path}", params={"ref": branch})
        if response.status_code == 404:
            return None
        self._check(response)
        return response.json().get("sha")

    async def commit_file(self, repo: str, path: str, content: str, message: str,
                          branch: str, sha: str | None) -> dict:
        """Create or update a file in one commit. Returns the commit payload."""
        body: dict = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha:
            body["sha"] = sha
        async with http_client(timeout=TIMEOUT, headers=self.headers) as client:
            response = await client.put(f"{API}/repos/{repo}/contents/{path}", json=body)
        self._check(response)
        return response.json()

    def _check(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                details = response.json()
            except ValueError:
                details = {"body": response.text[:300]}
            raise UpstreamError(
                "github.api_error",
                f"GitHub API returned {response.status_code}",
                details=details,
            )

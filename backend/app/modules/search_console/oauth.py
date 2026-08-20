"""Google OAuth 2.0 for Search Console (desktop loopback flow).

Credentials are passed in by the caller (the service resolves them from the
settings table with an env fallback) so they can be configured from the UI.
"""
from urllib.parse import urlencode

import httpx

from app.core.http import http_client

from app.core.exceptions import AppError

AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
# Search Console + Google Analytics (read-only). New consents cover both;
# older tokens may need a reconnect to gain the analytics scope.
SCOPES = (
    "https://www.googleapis.com/auth/webmasters.readonly "
    "https://www.googleapis.com/auth/analytics.readonly"
)
REDIRECT_URI = "http://127.0.0.1:8317/api/search-console/oauth/callback"


def is_configured(client_id: str, client_secret: str) -> bool:
    return bool(client_id and client_secret)


def build_consent_url(client_id: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_URI}?{urlencode(params)}"


async def exchange_code(code: str, client_id: str, client_secret: str) -> dict:
    async with http_client(timeout=20.0) as client:
        response = await client.post(
            TOKEN_URI,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if response.status_code != 200:
        raise AppError("search_console.oauth_failed", "Token exchange failed", details=response.json())
    return response.json()


async def refresh_token(refresh: str, client_id: str, client_secret: str) -> dict:
    async with http_client(timeout=20.0) as client:
        response = await client.post(
            TOKEN_URI,
            data={
                "refresh_token": refresh,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
            },
        )
    if response.status_code != 200:
        raise AppError("search_console.oauth_failed", "Token refresh failed", details=response.json())
    return response.json()

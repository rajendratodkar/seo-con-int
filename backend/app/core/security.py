"""Local API token guard.

The backend binds to 127.0.0.1 only. When SCI_BACKEND_TOKEN is set, every
non-health request must carry it in X-Backend-Token. Tauri passes the token
to the frontend at launch.
"""
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

PUBLIC_PATHS = ("/api/health", "/docs", "/openapi.json", "/redoc")


def generate_token() -> str:
    return secrets.token_urlsafe(32)


class TokenGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = settings.backend_token
        if token and not request.url.path.startswith(PUBLIC_PATHS):
            provided = request.headers.get("X-Backend-Token", "")
            if not secrets.compare_digest(provided, token):
                return JSONResponse(
                    status_code=401,
                    content={"error": {"code": "auth.invalid_token", "message": "Missing or invalid token", "details": {}}},
                )
        return await call_next(request)

"""Application error model.

Every error surfaces as a single envelope:
    { "error": { "code": "<module>.<reason>", "message": "...", "details": {} } }
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Business error with a namespaced code."""

    def __init__(self, code: str, message: str, status: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status=404)


class ConflictError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status=409)


class UpstreamError(AppError):
    """External integration failure (Google, WordPress, ...)."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(code, message, status=502, details=details)


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_envelope("internal.error", f"Unexpected error: {type(exc).__name__}"),
        )

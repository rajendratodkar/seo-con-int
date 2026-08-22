"""FastAPI application entrypoint.

Runs as a local sidecar managed by Tauri (127.0.0.1 only).
"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import ensure_data_dirs, settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.security import TokenGuardMiddleware, generate_token
from app.database.connection import apply_schema


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    setup_logging()
    ensure_data_dirs()
    apply_schema()
    _init_sentry()
    # Seed reference data and rules once (idempotent)
    from app.database.seeds import run_seeds

    run_seeds()
    # Publish the per-launch token for the frontend
    token = settings.backend_token or generate_token()
    (settings.data_dir / "runtime" / "backend_token.txt").write_text(token, encoding="utf-8")
    (settings.data_dir / "runtime" / "backend_info.json").write_text(
        json.dumps({"host": settings.backend_host, "port": settings.backend_port}), encoding="utf-8"
    )
    yield


def _init_sentry() -> None:
    """Crash reporting — only active when SCI_SENTRY_DSN is configured."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=settings.sentry_dsn, release=settings.app_version, traces_sample_rate=0.0)
    except Exception:  # noqa: BLE001 — telemetry must never break the app
        pass


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=app_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TokenGuardMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

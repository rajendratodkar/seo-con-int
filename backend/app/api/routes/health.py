"""Health endpoint — used by Tauri to know when the backend is ready."""
from fastapi import APIRouter

from app.core.config import settings
from app.database.connection import db_ok

router = APIRouter()


@router.get("/")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "database": "ok" if db_ok() else "error",
    }

"""Diagnostics HTTP layer: usage events, crash reports, system info."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession
from app.modules.diagnostics.service import DiagnosticsService

router = APIRouter()


class TrackPayload(BaseModel):
    event: str = Field(pattern="^(page_view|action|crash)$")
    detail: str | None = None


class CrashPayload(BaseModel):
    message: str
    stack: str | None = None
    route: str | None = None


@router.post("/events")
def track(db: DbSession, payload: TrackPayload):
    DiagnosticsService(db).track(payload.event, payload.detail)
    return {"ok": True}


@router.get("/events")
def list_events(db: DbSession, limit: int = 100):
    return DiagnosticsService(db).list_events(limit)


@router.post("/crash")
def report_crash(db: DbSession, payload: CrashPayload):
    DiagnosticsService(db).report_crash(payload.message, payload.stack, payload.route)
    return {"ok": True}


@router.get("/info")
def info(db: DbSession):
    return DiagnosticsService(db).info()

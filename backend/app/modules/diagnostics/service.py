"""Diagnostics service — local usage analytics, crash capture, system info.

Privacy posture: everything stays on-device in SQLite + log files; Sentry is
only used when the user explicitly configured SCI_SENTRY_DSN.
"""
import logging
import platform

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.http import check_internet
from app.modules.diagnostics.repository import DiagnosticsRepository

logger = logging.getLogger(__name__)

ALLOWED_EVENT_KINDS = ("page_view", "action", "crash")
MAX_DETAIL_LEN = 300


class DiagnosticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DiagnosticsRepository(db)

    # -- usage analytics ---------------------------------------------------------
    def track(self, event_kind: str, detail: str | None) -> None:
        if event_kind not in ALLOWED_EVENT_KINDS:
            raise AppError("diagnostics.invalid_event", f"Unknown event kind: {event_kind}")
        self.repo.insert_event(event_kind, (detail or "")[:MAX_DETAIL_LEN] or None)

    def list_events(self, limit: int) -> dict:
        return {"items": self.repo.list_events(min(limit, 500)), "counts": self.repo.counts()}

    # -- crash reporting ---------------------------------------------------------
    def report_crash(self, message: str, stack: str | None, route: str | None) -> None:
        logger.error("CRASH report route=%s: %s\n%s", route, message[:500], (stack or "")[:2000])
        self.repo.insert_event("crash", f"{route or '?'}: {message[:200]}")
        self._forward_to_sentry(message, stack, route)

    def _forward_to_sentry(self, message: str, stack: str | None, route: str | None) -> None:
        if not settings.sentry_dsn:
            return
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                scope.set_tag("route", route or "unknown")
                sentry_sdk.capture_message(f"{message[:500]}\n{stack or ''}"[:3000], level="error")
        except Exception:  # noqa: BLE001 — telemetry must never break the app
            pass

    # -- system info (offline detection etc.) -------------------------------------
    def info(self) -> dict:
        logfile = settings.data_dir / "runtime" / "backend.log"
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()}",
            "online": check_internet(),
            "proxy_configured": bool(settings.http_proxy or settings.https_proxy),
            "sentry_enabled": bool(settings.sentry_dsn),
            "data_dir": str(settings.data_dir),
            "log_file": str(logfile),
            "log_size_bytes": logfile.stat().st_size if logfile.exists() else 0,
        }

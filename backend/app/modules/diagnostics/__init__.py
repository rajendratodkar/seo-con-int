"""Diagnostics module — local usage analytics, crash reporting, system info."""
from app.modules.diagnostics.router import router as diagnostics_router

__all__ = ["diagnostics_router"]

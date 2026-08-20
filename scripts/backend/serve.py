"""Run the FastAPI backend (entry point used by the Tauri desktop shell).

Usage:  python scripts/backend/serve.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

import uvicorn  # noqa: E402

from app.core.config import settings  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        log_level="info",
    )

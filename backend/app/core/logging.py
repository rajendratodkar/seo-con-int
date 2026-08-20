"""Logging setup — console + rotating file under data/runtime/."""
import logging
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    logfile = settings.data_dir / "runtime" / "backend.log"
    logfile.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Quiet noisy clients
    logging.getLogger("httpx").setLevel(logging.WARNING)
    _configured = True

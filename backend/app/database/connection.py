"""SQLite connection management.

The schema DDL (database/schema/schema_v1.sql) is the single source of truth;
repositories query through SQLAlchemy Sessions using parameterized SQL.
Rule 4: no calculations in the database layer.
"""
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine = None
_SessionFactory = None


def _fk_pragma_on_connect(dbapi_conn, _record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine():
    global _engine, _SessionFactory
    if _engine is None:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{settings.database_path}", future=True)
        event.listen(_engine, "connect", _fk_pragma_on_connect)
        _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    session = _SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def apply_schema(schema_path: Path | None = None) -> None:
    """Idempotent bootstrap — executes the versioned DDL (IF NOT EXISTS everywhere)."""
    path = schema_path or settings.schema_path
    ddl = path.read_text(encoding="utf-8")
    # Also load extension schemas (e.g. monitoring)
    schema_dir = path.parent
    for ext in sorted(schema_dir.glob("schema_v1_*.sql")):
        ddl += "\n" + ext.read_text(encoding="utf-8")
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.database_path)
    try:
        con.executescript(ddl)  # multi-statement DDL requires executescript
        con.commit()
    finally:
        con.close()


def db_ok() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

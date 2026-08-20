"""Add monitoring & alerts tables to an existing SQLite database.

Run: python scripts/database/migrate_monitoring.py
"""
import os
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMA_PATH = os.path.join(ROOT, "database", "schema", "schema_v1_monitoring.sql")
DB_PATH = os.path.join(ROOT, "data", "sci.db")


def migrate() -> None:
    if not os.path.exists(SCHEMA_PATH):
        print(f"Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("The monitoring tables will be created when the app first boots.")
        sys.exit(0)

    with open(SCHEMA_PATH, "r") as f:
        sql = f.read()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(sql)
        conn.commit()
        print("✅ Monitoring tables created / verified successfully.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

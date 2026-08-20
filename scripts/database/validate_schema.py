"""Validate database/schema/schema_v1.sql executes cleanly on SQLite."""
import sqlite3
from pathlib import Path

sql = Path("database/schema/schema_v1.sql").read_text(encoding="utf-8")
con = sqlite3.connect(":memory:")
con.executescript(sql)

tables = [
    r[0]
    for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
]
indexes = [
    r[0]
    for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='index' "
        "AND name LIKE 'idx_%' ORDER BY name"
    )
]
print(f"OK: {len(tables)} tables, {len(indexes)} indexes")
for t in tables:
    print(" -", t)

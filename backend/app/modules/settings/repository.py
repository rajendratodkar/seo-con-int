"""Settings + AI providers persistence (SQL only)."""
from sqlalchemy import text
from sqlalchemy.orm import Session


class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    # -- ai_providers ------------------------------------------------------------
    def upsert_provider(self, provider: str, fields: dict) -> int:
        row = self.db.execute(
            text("SELECT id FROM ai_providers WHERE provider = :p"), {"p": provider}
        ).first()
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        if row:
            self.db.execute(
                text(f"UPDATE ai_providers SET {sets}, updated_at = datetime('now') WHERE id = :id"),
                {**fields, "id": row[0]},
            )
            self.db.commit()
            return row[0]
        result = self.db.execute(
            text(
                "INSERT INTO ai_providers (provider, display_name, api_key_encrypted, model, is_default, enabled, config) "
                "VALUES (:provider, :display_name, :api_key_encrypted, :model, :is_default, :enabled, :config)"
            ),
            {
                "provider": provider,
                "display_name": fields.get("display_name", provider.title()),
                "api_key_encrypted": fields.get("api_key_encrypted"),
                "model": fields.get("model"),
                "is_default": fields.get("is_default", 0),
                "enabled": fields.get("enabled", 0),
                "config": fields.get("config"),
            },
        )
        self.db.commit()
        return result.lastrowid

    def get_provider(self, provider: str) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM ai_providers WHERE provider = :p"), {"p": provider}
        ).mappings().first()
        return dict(row) if row else None

    def list_providers(self) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM ai_providers ORDER BY is_default DESC, provider")
        ).mappings().all()
        return [dict(r) for r in rows]

    def clear_default_flags(self, except_provider: str | None = None) -> None:
        self.db.execute(
            text("UPDATE ai_providers SET is_default = 0 WHERE provider != :p"),
            {"p": except_provider or ""},
        )
        self.db.commit()

    # -- settings ------------------------------------------------------------------
    def get_setting(self, key: str) -> str | None:
        row = self.db.execute(text("SELECT value FROM settings WHERE key = :k"), {"k": key}).first()
        return row[0] if row else None

    def set_setting(self, key: str, value: str) -> None:
        self.db.execute(
            text(
                "INSERT INTO settings (key, value) VALUES (:k, :v) "
                "ON CONFLICT(key) DO UPDATE SET value = :v, updated_at = datetime('now')"
            ),
            {"k": key, "v": value},
        )
        self.db.commit()

    def list_settings(self) -> list[dict]:
        rows = self.db.execute(text("SELECT key, value, updated_at FROM settings ORDER BY key")).mappings().all()
        return [dict(r) for r in rows]

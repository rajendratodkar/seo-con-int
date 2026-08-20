"""Settings + AI provider management. API keys are encrypted at rest (crypto.py)."""
import json

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.exceptions import AppError, NotFoundError
from app.modules.settings.repository import SettingsRepository

KNOWN_PROVIDERS = ("openai", "gemini", "anthropic")


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SettingsRepository(db)

    # -- AI providers ------------------------------------------------------------
    def list_providers(self) -> list[dict]:
        providers = self.repo.list_providers()
        return [self._public(row) for row in providers]

    def save_provider(
        self, provider: str, api_key: str | None, model: str | None,
        enabled: bool, is_default: bool,
    ) -> dict:
        if provider not in KNOWN_PROVIDERS:
            raise AppError("settings.unknown_provider", f"Provider must be one of {KNOWN_PROVIDERS}")
        if is_default:
            self.repo.clear_default_flags(provider)
        fields = {
            "model": model,
            "enabled": 1 if enabled else 0,
            "is_default": 1 if is_default else 0,
        }
        if api_key:
            fields["api_key_encrypted"] = encrypt_secret(api_key)
        self.repo.upsert_provider(provider, fields)
        return self._get_public(provider)

    def _get_public(self, provider: str) -> dict:
        row = self.repo.get_provider(provider)
        if row is None:
            raise NotFoundError("settings.provider_not_found", f"Provider {provider} is not configured")
        return self._public(row)

    @staticmethod
    def _public(row: dict) -> dict:
        return {
            "id": row["id"],
            "provider": row["provider"],
            "display_name": row["display_name"],
            "model": row["model"],
            "is_default": bool(row["is_default"]),
            "enabled": bool(row["enabled"]),
            "has_api_key": bool(row.get("api_key_encrypted")),
        }

    def resolve_credentials(self, provider: str | None) -> dict:
        """Returns {provider, api_key, model} for the requested/default provider."""
        row = None
        if provider:
            row = self.repo.get_provider(provider)
        if row is None:
            for candidate in self.repo.list_providers():
                if candidate["is_default"] and candidate["enabled"]:
                    row = candidate
                    break
        if row is None:
            for candidate in self.repo.list_providers():
                if candidate["enabled"]:
                    row = candidate
                    break
        if row is None or not row.get("api_key_encrypted"):
            raise AppError("ai.not_configured", "No enabled AI provider with an API key. Configure one in Settings → AI.")
        api_key = decrypt_secret(row["api_key_encrypted"])
        if api_key is None:
            raise AppError("ai.key_corrupt", "Stored API key could not be decrypted — re-enter it in Settings → AI.")
        return {"provider": row["provider"], "api_key": api_key, "model": row["model"]}

    # -- generic settings ----------------------------------------------------------
    def get(self, key: str) -> str | None:
        return self.repo.get_setting(key)

    def set(self, key: str, value) -> None:
        self.repo.set_setting(key, value if isinstance(value, str) else json.dumps(value))

    def list_all(self) -> list[dict]:
        return self.repo.list_settings()

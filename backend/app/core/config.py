"""Application settings (pydantic-settings, env prefix SCI_)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCI_", env_file=".env", extra="ignore")

    app_name: str = "SEO Content Intelligence"
    app_version: str = "0.1.0"

    backend_host: str = "127.0.0.1"
    backend_port: int = 8317

    data_dir: Path = PROJECT_ROOT / "data"
    database_path: Path = PROJECT_ROOT / "data" / "sci.db"
    schema_path: Path = PROJECT_ROOT / "database" / "schema" / "schema_v1.sql"

    # Optional local API token; empty disables the check (dev mode)
    backend_token: str = ""

    # Network: custom proxies respected by every outbound HTTP client
    http_proxy: str = ""
    https_proxy: str = ""

    # Crash reporting (optional; disabled when empty)
    sentry_dsn: str = ""

    # Google OAuth (Phase 3)
    google_client_id: str = ""
    google_client_secret: str = ""

    # AI providers (Phase 8)
    openai_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""


settings = Settings()


def ensure_data_dirs() -> None:
    """Create the data/ subtree (raw is kept forever — Rule 7)."""
    for sub in ("raw", "processed", "cache", "exports", "backups", "runtime"):
        (settings.data_dir / sub).mkdir(parents=True, exist_ok=True)

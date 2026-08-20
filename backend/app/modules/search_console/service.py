"""Search Console orchestration: OAuth state, tokens, imports, analytics."""
import json
import secrets
import time

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.modules.search_console import oauth
from app.modules.search_console.analytics import SearchConsoleAnalytics
from app.modules.search_console.api_client import SearchConsoleClient
from app.modules.search_console.importer import SearchConsoleImporter
from app.modules.search_console.normalizer import normalize_manual_rows
from app.modules.search_console.repository import SearchConsoleRepository

TOKEN_KEY = "google_oauth"


class ManualImportRow(BaseModel):
    date: str
    query: str | None = None
    page_url: str | None = None
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    position: float = 0.0


class ManualImportPayload(BaseModel):
    website_id: int
    site_url: str
    rows: list[ManualImportRow]


class SearchConsoleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SearchConsoleRepository(db)
        self.importer = SearchConsoleImporter(db)
        self.analytics = SearchConsoleAnalytics(db)

    # --- OAuth -----------------------------------------------------------------

    def consent_url(self) -> dict:
        client_id, client_secret = self._credentials()
        if not oauth.is_configured(client_id, client_secret):
            # Not an error — the UI shows guidance (Settings → Google) instead.
            return {"url": None, "auth_url": None, "configured": False}
        state = secrets.token_urlsafe(16)
        self._save_setting("google_oauth_state", state)
        url = oauth.build_consent_url(client_id, state)
        return {"url": url, "auth_url": url, "configured": True}

    async def handle_callback(self, code: str, state: str) -> dict:
        expected = self._read_setting("google_oauth_state")
        if not expected or expected != state:
            raise AppError("search_console.bad_state", "OAuth state mismatch")
        client_id, client_secret = self._credentials()
        tokens = await oauth.exchange_code(code, client_id, client_secret)
        self._store_tokens(tokens)
        return {"status": "connected"}

    def status(self) -> dict:
        client_id, client_secret = self._credentials()
        return {
            "configured": oauth.is_configured(client_id, client_secret),
            "connected": self._read_setting(TOKEN_KEY) is not None,
            "redirect_uri": oauth.REDIRECT_URI,
        }

    # --- Google client configuration (stored in settings, env fallback) ---------

    def get_config(self) -> dict:
        client_id, client_secret = self._credentials()
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": oauth.REDIRECT_URI,
        }

    def save_config(self, client_id: str, client_secret: str) -> dict:
        self._save_setting("google_client_id", client_id.strip())
        self._save_setting("google_client_secret", client_secret.strip())
        return {"saved": True}

    def _credentials(self) -> tuple[str, str]:
        """UI-stored credentials win; env vars (.env / SCI_GOOGLE_*) are the fallback."""
        client_id = self._read_setting("google_client_id") or settings.google_client_id
        client_secret = self._read_setting("google_client_secret") or settings.google_client_secret
        return client_id or "", client_secret or ""

    def _store_tokens(self, tokens: dict) -> None:
        # Persist an absolute expiry so _access_token() can refresh proactively.
        tokens = dict(tokens)
        tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600)) - 120
        self._save_setting(TOKEN_KEY, json.dumps(tokens))

    async def _access_token(self) -> str:
        raw = self._read_setting(TOKEN_KEY)
        if not raw:
            raise AppError("search_console.not_connected", "Connect a Google account first")
        tokens = json.loads(raw)
        if tokens.get("expires_at", 0) <= time.time() and tokens.get("refresh_token"):
            client_id, client_secret = self._credentials()
            refreshed = await oauth.refresh_token(tokens["refresh_token"], client_id, client_secret)
            # Google may omit refresh_token on refresh — keep the old one.
            refreshed.setdefault("refresh_token", tokens["refresh_token"])
            self._store_tokens(refreshed)
            tokens = refreshed
        return tokens["access_token"]

    # --- properties --------------------------------------------------------------

    async def discover_properties(self) -> list[dict]:
        client = SearchConsoleClient(await self._access_token())
        sites = await client.list_sites()
        discovered = []
        for site in sites:
            prop_id = self.repo.upsert_property(
                site["siteUrl"], None, site.get("permissionLevel"), "discovered"
            )
            discovered.append({**site, "id": prop_id})
        return discovered

    def connect_property(self, property_id: int, website_id: int) -> dict:
        prop = self.repo.get_property(property_id)
        if not prop:
            raise NotFoundError("search_console.property_not_found", f"Property {property_id} does not exist")
        self.repo.upsert_property(prop["site_url"], website_id, prop["permission_level"], "connected")
        return self.repo.get_property(property_id)

    def list_properties(self) -> list[dict]:
        return self.repo.list_properties()

    # --- imports -------------------------------------------------------------------

    async def sync(self, property_id: int, mode: str) -> dict:
        prop = self.repo.get_property(property_id)
        if not prop or not prop["website_id"]:
            raise NotFoundError("search_console.not_connected", "Property is not connected to a website")
        if mode == "historical":
            start, end = self.importer.historical_window()
        else:
            start, end = self.importer.incremental_window()
        imported = await self.importer.import_range(
            property_id, prop["website_id"], await self._access_token(), start, end, mode
        )
        return {"imported": imported, "window": {"start": start, "end": end}}

    def manual_import(self, payload: ManualImportPayload) -> dict:
        """Import exported CSV rows without OAuth — same raw-first pipeline."""
        property_id = self.repo.upsert_property(payload.site_url, payload.website_id, None, "connected")
        rows = normalize_manual_rows([r.model_dump() for r in payload.rows])
        self.repo.store_raw(
            property_id, None,
            {"source": "manual"},
            {"rows": [r.model_dump() for r in payload.rows]},
        )
        imported = self.repo.upsert_rows(payload.website_id, property_id, rows)
        self.db.commit()
        return {"imported": imported, "property_id": property_id}

    # --- analytics -------------------------------------------------------------------

    def stats(self, website_id: int | None) -> dict:
        return self.repo.data_stats(website_id)

    def queries(self, website_id: int, start: str, end: str, limit: int) -> list[dict]:
        return self.analytics.top_queries(website_id, start, end, limit)

    def pages(self, website_id: int, start: str, end: str, limit: int) -> list[dict]:
        return self.analytics.top_pages(website_id, start, end, limit)

    def compare(self, website_id: int, cs: str, ce: str, ps: str, pe: str) -> dict:
        return self.analytics.compare_periods(website_id, cs, ce, ps, pe)

    # --- settings helpers ---------------------------------------------------------------

    def _save_setting(self, key: str, value: str) -> None:
        self.db.execute(
            text(
                "INSERT INTO settings (key, value) VALUES (:key, :value) "
                "ON CONFLICT (key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')"
            ),
            {"key": key, "value": value},
        )
        self.db.commit()

    def _read_setting(self, key: str) -> str | None:
        return self.db.execute(text("SELECT value FROM settings WHERE key = :key"), {"key": key}).scalar_one_or_none()

"""Settings HTTP layer (app settings + AI providers)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import DbSession
from app.modules.settings.service import SettingsService

router = APIRouter()


class ProviderSave(BaseModel):
    provider: str = Field(pattern="^(openai|gemini|anthropic)$")
    api_key: str | None = None  # omitted = keep existing key
    model: str | None = None
    enabled: bool = False
    is_default: bool = False


class SettingPut(BaseModel):
    value: str


@router.get("/ai-providers")
def list_providers(db: DbSession):
    items = SettingsService(db).list_providers()
    return {"items": items, "total": len(items)}


@router.put("/ai-providers/{provider}")
def save_provider(db: DbSession, provider: str, payload: ProviderSave):
    return SettingsService(db).save_provider(
        provider, payload.api_key, payload.model, payload.enabled, payload.is_default
    )


@router.get("/values")
def list_settings(db: DbSession):
    items = SettingsService(db).list_all()
    return {"items": items, "total": len(items)}


@router.get("/values/{key}")
def get_setting(db: DbSession, key: str):
    return {"key": key, "value": SettingsService(db).get(key)}


@router.put("/values/{key}")
def put_setting(db: DbSession, key: str, payload: SettingPut):
    SettingsService(db).set(key, payload.value)
    return {"key": key, "value": payload.value}

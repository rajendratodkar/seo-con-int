"""Google Analytics HTTP layer."""
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.dependencies import DbSession
from app.modules.google_analytics.service import GoogleAnalyticsService

router = APIRouter()


class ConnectPayload(BaseModel):
    website_id: int
    property_id: str
    property_name: str | None = None


@router.get("/properties")
async def list_properties(db: DbSession):
    items = await GoogleAnalyticsService(db).list_properties()
    return {"items": items, "total": len(items)}


@router.post("/connect")
def connect(db: DbSession, payload: ConnectPayload):
    return GoogleAnalyticsService(db).connect(payload.website_id, payload.property_id, payload.property_name)


@router.get("/connection")
def get_connection(db: DbSession, website_id: int = Query(...)):
    return {"connection": GoogleAnalyticsService(db).get_connection(website_id)}


@router.delete("/connection")
def disconnect(db: DbSession, website_id: int = Query(...)):
    return GoogleAnalyticsService(db).disconnect(website_id)


@router.post("/sync")
async def sync(db: DbSession, website_id: int = Query(...), days: int = Query(default=28, ge=1, le=365)):
    return await GoogleAnalyticsService(db).sync(website_id, days)


@router.get("/summary")
def summary(db: DbSession, website_id: int = Query(...), days: int = Query(default=28, ge=1, le=365)):
    return GoogleAnalyticsService(db).summary(website_id, days)

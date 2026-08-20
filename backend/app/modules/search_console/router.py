"""Search Console HTTP layer."""
from datetime import date, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.api.dependencies import DbSession
from app.modules.search_console.service import ManualImportPayload, SearchConsoleService

router = APIRouter()


def _service(db: DbSession) -> SearchConsoleService:
    return SearchConsoleService(db)


# --- OAuth ---------------------------------------------------------------------

@router.get("/oauth/url")
def oauth_url(db: DbSession):
    return _service(db).consent_url()


@router.get("/oauth/status")
def oauth_status(db: DbSession):
    return _service(db).status()


class GoogleClientConfig(BaseModel):
    client_id: str = ""
    client_secret: str = ""


@router.get("/oauth/config")
def get_oauth_config(db: DbSession):
    return _service(db).get_config()


@router.put("/oauth/config")
def save_oauth_config(payload: GoogleClientConfig, db: DbSession):
    return _service(db).save_config(payload.client_id, payload.client_secret)


@router.get("/oauth/callback")
async def oauth_callback(db: DbSession, code: str = Query(...), state: str = Query(...)):
    await _service(db).handle_callback(code, state)
    # Shown in the browser tab Google redirects to — keep it human-friendly.
    return HTMLResponse(
        "<!doctype html><html><body style='font-family:system-ui,sans-serif;display:flex;"
        "align-items:center;justify-content:center;height:100vh;margin:0;background:#f6f7f9'>"
        "<div style='text-align:center;background:#fff;border:1px solid #e2e5ea;border-radius:10px;"
        "padding:32px 48px;max-width:420px'>"
        "<h2 style='margin:0 0 8px;color:#1a7f37'>&#10003; Google account connected</h2>"
        "<p style='color:#4b5563'>You can close this tab. Back in the app, click "
        "<strong>Discover properties</strong>, then connect a property to your website.</p>"
        "<p style='color:#9ca3af;font-size:13px'>This window closes automatically.</p>"
        "</div><script>setTimeout(function(){window.close()},5000)</script></body></html>"
    )


# --- properties ------------------------------------------------------------------

@router.get("/properties")
def list_properties(db: DbSession):
    return {"items": _service(db).list_properties()}


@router.get("/properties/discover")
async def discover_properties(db: DbSession):
    return {"items": await _service(db).discover_properties()}


@router.post("/properties/{property_id}/connect")
def connect_property(property_id: int, db: DbSession, website_id: int = Query(...)):
    return _service(db).connect_property(property_id, website_id)


# --- imports -----------------------------------------------------------------------

@router.post("/sync")
async def sync(db: DbSession, property_id: int = Query(...), mode: str = Query("incremental")):
    return await _service(db).sync(property_id, mode)


@router.post("/import/manual")
def manual_import(payload: ManualImportPayload, db: DbSession):
    return _service(db).manual_import(payload)


# --- analytics -------------------------------------------------------------------------

@router.get("/stats")
def stats(db: DbSession, website_id: int | None = Query(None)):
    return _service(db).stats(website_id)


@router.get("/queries")
def queries(
    db: DbSession,
    website_id: int = Query(...),
    start: str = Query((date.today() - timedelta(days=28)).isoformat()),
    end: str = Query(date.today().isoformat()),
    limit: int = Query(50, ge=1, le=500),
):
    return {"items": _service(db).queries(website_id, start, end, limit)}


@router.get("/pages")
def pages(
    db: DbSession,
    website_id: int = Query(...),
    start: str = Query((date.today() - timedelta(days=28)).isoformat()),
    end: str = Query(date.today().isoformat()),
    limit: int = Query(50, ge=1, le=500),
):
    return {"items": _service(db).pages(website_id, start, end, limit)}


@router.get("/compare")
def compare(
    db: DbSession,
    website_id: int = Query(...),
    current_start: str = Query(...),
    current_end: str = Query(...),
    previous_start: str = Query(...),
    previous_end: str = Query(...),
):
    return _service(db).compare(website_id, current_start, current_end, previous_start, previous_end)

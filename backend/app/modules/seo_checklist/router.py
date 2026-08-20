"""SEO Checklist HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.seo_checklist.schemas import ChecklistCreate, ChecklistItemAdd, ChecklistItemUpdate
from app.modules.seo_checklist.service import ChecklistService

router = APIRouter()


def _svc(db: DbSession) -> ChecklistService:
    return ChecklistService(db)


@router.post("", status_code=201)
def create_checklist(payload: ChecklistCreate, db: DbSession):
    """Get or create a checklist for a page."""
    return _svc(db).get_or_create(payload.website_id, payload.page_id)


@router.get("")
def list_checklists(db: DbSession, website_id: int = Query(...)):
    """List all checklists for a website."""
    return _svc(db).list(website_id)


@router.get("/{checklist_id}")
def get_checklist(checklist_id: int, db: DbSession):
    """Get checklist detail with all items."""
    return _svc(db).detail(checklist_id)


@router.post("/{checklist_id}/auto-generate")
def auto_generate(checklist_id: int, db: DbSession):
    """Auto-populate checklist from SEO findings."""
    return _svc(db).auto_generate(checklist_id)


@router.post("/{checklist_id}/items", status_code=201)
def add_item(checklist_id: int, payload: ChecklistItemAdd, db: DbSession):
    """Add a manual item to a checklist."""
    return _svc(db).add_item(checklist_id, payload.category, payload.item_text, payload.notes)


@router.patch("/items/{item_id}")
def update_item(item_id: int, payload: ChecklistItemUpdate, db: DbSession):
    """Update a checklist item (status, notes)."""
    return _svc(db).update_item(item_id, payload.status, payload.notes)


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: DbSession):
    """Delete a checklist item."""
    return _svc(db).delete_item(item_id)


@router.post("/{checklist_id}/complete")
def complete_checklist(checklist_id: int, db: DbSession):
    """Mark a checklist as completed."""
    return _svc(db).complete_checklist(checklist_id)


@router.delete("/{checklist_id}")
def delete_checklist(checklist_id: int, db: DbSession):
    """Delete a checklist."""
    return _svc(db).delete_checklist(checklist_id)

"""Schema Markup HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.schema_markup.schemas import GenerateRequest, SaveSchemaRequest, ValidateRequest
from app.modules.schema_markup.service import SchemaMarkupService
from app.modules.schema_markup.generators import GENERATORS

router = APIRouter()


def _svc(db: DbSession) -> SchemaMarkupService:
    return SchemaMarkupService(db)


@router.get("/types")
def list_types():
    """List available schema types."""
    return {"types": list(GENERATORS.keys())}


@router.post("/generate")
def generate_schema(payload: GenerateRequest, db: DbSession):
    """Generate a JSON-LD schema from parameters."""
    return _svc(db).generate(payload.schema_type, payload.page_id, payload.params)


@router.post("/validate")
def validate_schema(payload: ValidateRequest, db: DbSession):
    """Validate a JSON-LD string."""
    return _svc(db).validate(payload.json_ld)


@router.post("/save")
def save_schema(payload: SaveSchemaRequest, db: DbSession):
    """Save a JSON-LD schema for a page."""
    return _svc(db).save(payload.page_id, payload.schema_type, payload.json_ld)


@router.get("/page/{page_id}")
def list_for_page(page_id: int, db: DbSession):
    """List saved schemas for a page."""
    return _svc(db).list_for_page(page_id)


@router.get("/{schema_id}")
def get_schema(schema_id: int, db: DbSession):
    """Get a saved schema."""
    return _svc(db).get(schema_id)


@router.delete("/{schema_id}")
def delete_schema(schema_id: int, db: DbSession):
    """Delete a saved schema."""
    return _svc(db).delete(schema_id)


@router.get("/coverage/summary")
def coverage_summary(db: DbSession, website_id: int = Query(...)):
    """Get schema coverage stats for a website."""
    return _svc(db).coverage(website_id)

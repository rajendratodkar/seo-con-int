"""Schema Markup service — generate, validate, and store JSON-LD schemas."""
import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.schema_markup.generators import GENERATORS
from app.modules.schema_markup.repository import SchemaRepository

logger = logging.getLogger(__name__)


def validate_json_ld(raw: str) -> list[str]:
    """Validate a JSON-LD string. Returns list of error messages (empty = valid)."""
    errors = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    if not isinstance(data, dict):
        return ["JSON-LD must be a JSON object"]

    # Check required fields
    if "@context" not in data:
        errors.append("Missing @context")
    elif data["@context"] != "https://schema.org":
        errors.append(f"@context should be 'https://schema.org', got '{data['@context']}'")

    if "@type" not in data:
        errors.append("Missing @type")

    # Type-specific validation
    schema_type = data.get("@type", "")
    if schema_type == "Article":
        if "headline" not in data:
            errors.append("Article missing headline")
        if "datePublished" not in data:
            errors.append("Article missing datePublished")
    elif schema_type == "FAQPage":
        entities = data.get("mainEntity", [])
        if not entities:
            errors.append("FAQPage missing mainEntity items")
        for i, entity in enumerate(entities):
            if entity.get("@type") != "Question":
                errors.append(f"mainEntity[{i}] should be @type Question")
            if "name" not in entity:
                errors.append(f"mainEntity[{i}] missing name")
            answer = entity.get("acceptedAnswer", {})
            if answer.get("@type") != "Answer":
                errors.append(f"mainEntity[{i}].acceptedAnswer should be @type Answer")
            if "text" not in answer:
                errors.append(f"mainEntity[{i}].acceptedAnswer missing text")
    elif schema_type == "HowTo":
        if "name" not in data:
            errors.append("HowTo missing name")
        steps = data.get("step", [])
        if not steps:
            errors.append("HowTo missing step items")
    elif schema_type == "Product":
        if "name" not in data:
            errors.append("Product missing name")
    elif schema_type == "BreadcrumbList":
        items = data.get("itemListElement", [])
        if not items:
            errors.append("BreadcrumbList missing itemListElement")
    elif schema_type == "Organization":
        if "name" not in data:
            errors.append("Organization missing name")

    return errors


class SchemaMarkupService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SchemaRepository(db)
        self.repo.ensure_table()

    def generate(self, schema_type: str, page_id: int | None, params: dict) -> dict:
        """Generate a JSON-LD schema from parameters."""
        generator = GENERATORS.get(schema_type)
        if not generator:
            raise NotFoundError("schema.unknown_type", f"Unknown schema type: {schema_type}")

        # If page_id provided, fill in defaults from page data
        if page_id and not params.get("title"):
            page = self.db.execute(
                text("SELECT * FROM pages WHERE id = :pid"), {"pid": page_id}
            ).mappings().one_or_none()
            if page:
                params.setdefault("title", page.get("title") or "")
                params.setdefault("description", page.get("meta_description"))
                params.setdefault("url", page.get("url"))
                # Check for existing schema on page
                existing = self.db.execute(
                    text("SELECT schema_json FROM page_content WHERE page_id = :pid"),
                    {"pid": page_id},
                ).mappings().one_or_none()
                if existing and existing.get("schema_json"):
                    try:
                        existing_schemas = json.loads(existing["schema_json"])
                        if isinstance(existing_schemas, list):
                            for s in existing_schemas:
                                if s.get("@type") == schema_type:
                                    return {"generated": s, "source": "existing_on_page"}
                    except (json.JSONDecodeError, TypeError):
                        pass

        schema = generator(**{k: v for k, v in params.items() if v is not None})
        return {"generated": schema, "source": "generated"}

    def validate(self, json_ld: str) -> dict:
        """Validate a JSON-LD string."""
        errors = validate_json_ld(json_ld)
        try:
            parsed = json.loads(json_ld) if json_ld.strip() else {}
        except json.JSONDecodeError:
            parsed = {}
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "schema_type": parsed.get("@type", "unknown"),
            "parsed": parsed,
        }

    def save(self, page_id: int, schema_type: str, json_ld: str) -> dict:
        """Save a JSON-LD schema for a page."""
        # Validate first
        errors = validate_json_ld(json_ld)
        return self.repo.save_schema(page_id, schema_type, json_ld, json.dumps(errors) if errors else None)

    def list_for_page(self, page_id: int) -> list[dict]:
        return self.repo.list_schemas_for_page(page_id)

    def get(self, schema_id: int) -> dict:
        s = self.repo.get_schema(schema_id)
        if not s:
            raise NotFoundError("schema.not_found", f"Schema {schema_id} not found")
        return s

    def delete(self, schema_id: int) -> dict:
        if not self.repo.delete_schema(schema_id):
            raise NotFoundError("schema.not_found", f"Schema {schema_id} not found")
        return {"deleted": True, "id": schema_id}

    def coverage(self, website_id: int) -> dict:
        return self.repo.get_page_schemas_summary(website_id)

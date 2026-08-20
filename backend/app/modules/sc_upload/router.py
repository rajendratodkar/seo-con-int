"""Search Console File Upload HTTP layer."""
from fastapi import APIRouter, File, Form, UploadFile, Query
from typing import Optional

from app.api.dependencies import DbSession
from app.modules.sc_upload.service import ScUploadService

router = APIRouter()


@router.post("/upload")
async def upload_sc_file(
    db: DbSession,
    file: UploadFile = File(...),
    website_id: int = Form(...),
    import_type: str = Form("performance"),
):
    """Upload a Search Console export file (CSV or JSON).

    Supported formats:
    - CSV: Google Search Console Performance report export
    - JSON: GSC API response format

    The data will be parsed, validated, and imported into the database.
    """
    content = await file.read()
    file_content = content.decode("utf-8")

    service = ScUploadService(db)
    result = service.parse_and_import(
        website_id=website_id,
        filename=file.filename or "upload.csv",
        file_content=file_content,
        import_type=import_type,
    )

    return result


@router.get("/imports")
def list_imports(
    db: DbSession,
    website_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
):
    """List import history for a website."""
    from app.modules.sc_upload.repository import ScUploadRepository
    repo = ScUploadRepository(db)
    return repo.list_imports(website_id, limit)


@router.get("/imports/{import_id}")
def get_import(db: DbSession, import_id: int):
    """Get details of a specific import."""
    from app.modules.sc_upload.repository import ScUploadRepository
    repo = ScUploadRepository(db)
    result = repo.get_import(import_id)
    if not result:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("import.not_found", f"Import {import_id} not found")
    return result


@router.get("/stats")
def get_import_stats(db: DbSession, website_id: int = Query(...)):
    """Get import statistics for a website."""
    from app.modules.sc_upload.repository import ScUploadRepository
    repo = ScUploadRepository(db)
    return repo.get_import_stats(website_id)

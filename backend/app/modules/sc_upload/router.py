"""Search Console File Upload HTTP layer."""
import csv
import io
from fastapi import APIRouter, File, Form, UploadFile, Query
from fastapi.responses import StreamingResponse
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


@router.delete("/imports/{import_id}")
def delete_import(db: DbSession, import_id: int):
    """Delete an import record and its associated data."""
    from app.modules.sc_upload.repository import ScUploadRepository
    repo = ScUploadRepository(db)
    result = repo.delete_import(import_id)
    if not result:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("import.not_found", f"Import {import_id} not found")
    return {"deleted": True, "import_id": import_id}


@router.get("/export")
def export_imports(db: DbSession, website_id: int = Query(...)):
    """Export import history as CSV."""
    from app.modules.sc_upload.repository import ScUploadRepository
    repo = ScUploadRepository(db)
    imports = repo.list_imports(website_id, limit=500)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Filename", "File Type", "Import Type", "Status",
                     "Rows Total", "Rows Imported", "Rows Skipped", "Rows Errors",
                     "Date Range Start", "Date Range End", "Created At", "Completed At"])

    for imp in imports:
        writer.writerow([
            imp.get("id"),
            imp.get("filename"),
            imp.get("file_type"),
            imp.get("import_type"),
            imp.get("status"),
            imp.get("rows_total", 0),
            imp.get("rows_imported", 0),
            imp.get("rows_skipped", 0),
            imp.get("rows_errors", 0),
            imp.get("date_range_start"),
            imp.get("date_range_end"),
            imp.get("created_at"),
            imp.get("completed_at"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sc_imports_{website_id}.csv"},
    )

"""Report Generator HTTP layer."""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, StreamingResponse

from app.api.dependencies import DbSession
from app.modules.report_generator.service import ReportGeneratorService
from app.modules.report_generator.schemas import ReportCreate

import io

router = APIRouter()


@router.post("")
def create_report(db: DbSession, data: ReportCreate):
    """Create and generate a new SEO audit report."""
    return ReportGeneratorService(db).create_and_generate(data)


@router.get("")
def list_reports(db: DbSession, website_id: int = Query(...)):
    """List all reports for a website."""
    return ReportGeneratorService(db).get_reports(website_id)


@router.get("/{report_id}")
def get_report(db: DbSession, report_id: int):
    """Get a specific report with its data."""
    return ReportGeneratorService(db).get_report(report_id)


@router.get("/{report_id}/sections")
def get_sections(db: DbSession, report_id: int):
    """Get all sections for a report."""
    return ReportGeneratorService(db).get_sections(report_id)


@router.get("/{report_id}/html", response_class=HTMLResponse)
def get_report_html(db: DbSession, report_id: int):
    """Get the rendered HTML report."""
    service = ReportGeneratorService(db)
    report = service.get_report(report_id)
    if report.get("report_data"):
        # Re-render from stored data
        from sqlalchemy import text
        website = db.execute(
            text("SELECT id, name, url FROM websites WHERE id = :id"),
            {"id": report["website_id"]},
        ).mappings().first()
        from app.modules.report_generator.schemas import ReportCreate
        config = ReportCreate(
            website_id=report["website_id"],
            title=report["title"],
            report_type=report["report_type"],
            format=report["format"],
            period_days=report["period_days"],
        )
        data = __import__("json").loads(report["report_data"])
        html = service._render_html(dict(website), data, config)
        return HTMLResponse(content=html)
    return HTMLResponse(content="<p>Report not yet generated.</p>", status_code=404)


@router.get("/{report_id}/pdf")
def get_report_pdf(db: DbSession, report_id: int):
    """Download report as PDF."""
    service = ReportGeneratorService(db)
    pdf_bytes = service.generate_pdf(report_id)
    report = service.get_report(report_id)
    
    filename = f"seo-report-{report_id}-{report['title'].replace(' ', '-').lower()[:50]}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/{report_id}")
def delete_report(db: DbSession, report_id: int):
    """Delete a report."""
    return ReportGeneratorService(db).delete_report(report_id)

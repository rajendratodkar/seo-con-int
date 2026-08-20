"""Report Generator service — orchestrates data collection and report rendering."""
import io
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.report_generator.repository import ReportGeneratorRepository
from app.modules.report_generator.schemas import ReportCreate


class ReportGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportGeneratorRepository(db)

    def create_and_generate(self, data: ReportCreate) -> dict:
        """Create a report and immediately generate it."""
        # Verify website exists
        website = self.repo.get_website(data.website_id)
        if not website:
            raise NotFoundError("website.not_found", f"Website {data.website_id} not found")

        # Create report
        report = self.repo.create_report(data)

        try:
            # Update status to generating
            self.repo.update_report_status(report["id"], "generating")

            # Collect all data
            report_data = self._collect_data(data.website_id, data.period_days)

            # Generate HTML
            html = self._render_html(website, report_data, data)

            # Store sections
            self._store_sections(report["id"], report_data)

            # Update report
            self.repo.update_report_status(
                report["id"],
                "completed",
                report_data=json.dumps(report_data),
            )

            report["status"] = "completed"
            report["report_data"] = json.dumps(report_data)

            return report

        except Exception as e:
            self.repo.update_report_status(report["id"], "failed")
            raise

    def get_report(self, report_id: int) -> dict:
        report = self.repo.get_report(report_id)
        if not report:
            raise NotFoundError("report.not_found", f"Report {report_id} not found")
        return report

    def get_reports(self, website_id: int) -> list[dict]:
        return self.repo.get_reports_by_website(website_id)

    def delete_report(self, report_id: int) -> bool:
        return self.repo.delete_report(report_id)

    def get_sections(self, report_id: int) -> list[dict]:
        return self.repo.get_sections(report_id)

    def generate_pdf(self, report_id: int) -> bytes:
        """Generate PDF from report data using xhtml2pdf."""
        from xhtml2pdf import pisa
        
        report = self.get_report(report_id)
        if not report.get("report_data"):
            raise NotFoundError("report.not_found", f"Report {report_id} has no data")
        
        # Get website info
        website = self.repo.get_website(report["website_id"])
        if not website:
            raise NotFoundError("website.not_found", f"Website {report['website_id']} not found")
        
        # Re-render HTML from stored data
        config = ReportCreate(
            website_id=report["website_id"],
            title=report["title"],
            report_type=report["report_type"],
            format=report["format"],
            period_days=report["period_days"],
        )
        data = json.loads(report["report_data"])
        html_content = self._render_html(website, data, config)
        
        # Generate PDF using xhtml2pdf
        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=output)
        
        if pisa_status.err:
            raise ValueError(f"PDF generation failed with {pisa_status.err} errors")
        
        return output.getvalue()

    # ------------------------------------------------------------------
    # Data Collection
    # ------------------------------------------------------------------

    def _collect_data(self, website_id: int, days: int) -> dict:
        """Collect all data for the report."""
        return {
            "overview": {
                "total_clicks": self.repo.get_traffic_summary(website_id, days)["total_clicks"],
                "total_impressions": self.repo.get_traffic_summary(website_id, days)["total_impressions"],
                "avg_ctr": self.repo.get_traffic_summary(website_id, days)["avg_ctr"],
                "avg_position": self.repo.get_traffic_summary(website_id, days)["avg_position"],
                "pages_indexed": self.repo.get_pages_count(website_id),
                "unique_queries": self.repo.get_keywords_count(website_id, days),
            },
            "traffic": {
                "trend": self.repo.get_traffic_trend(website_id, days),
            },
            "rankings": {
                "distribution": self.repo.get_ranking_distribution(website_id, days),
                "top_pages": self.repo.get_top_pages(website_id, days, 10),
                "top_queries": self.repo.get_top_queries(website_id, days, 10),
            },
            "findings": {
                "summary": self.repo.get_findings(website_id),
            },
        }

    def _store_sections(self, report_id: int, data: dict) -> None:
        """Store report sections for later retrieval."""
        sections = [
            ("overview", "Executive Summary", data["overview"]),
            ("traffic", "Traffic Analysis", data["traffic"]),
            ("rankings", "Rankings & Performance", data["rankings"]),
            ("findings", "SEO Findings", data["findings"]),
        ]
        for i, (stype, title, content) in enumerate(sections):
            self.repo.add_section(report_id, stype, title, json.dumps(content))

    # ------------------------------------------------------------------
    # HTML Rendering
    # ------------------------------------------------------------------

    def _render_html(self, website: dict, data: dict, config: ReportCreate) -> str:
        """Render a complete HTML report."""
        generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        overview = data["overview"]
        traffic = data["traffic"]
        rankings = data["rankings"]
        findings = data["findings"]

        # Build traffic chart data
        trend_html = self._render_traffic_chart(traffic.get("trend", []))

        # Build findings table
        findings_html = self._render_findings_table(findings.get("summary", []))

        # Build top pages table
        pages_html = self._render_top_pages_table(rankings.get("top_pages", []))

        # Build top queries table
        queries_html = self._render_top_queries_table(rankings.get("top_queries", []))

        # Build ranking distribution
        dist = rankings.get("distribution", {})
        total_kw = sum(dist.values()) if dist else 1
        dist_html = f"""
        <div class="ranking-dist">
            <div class="dist-bar">
                <div class="dist-segment top3" style="width: {(dist.get('top_3', 0) / total_kw * 100) if total_kw else 0}%">
                    Top 3: {dist.get('top_3', 0)}
                </div>
                <div class="dist-segment pos410" style="width: {(dist.get('pos_4_10', 0) / total_kw * 100) if total_kw else 0}%">
                    4-10: {dist.get('pos_4_10', 0)}
                </div>
                <div class="dist-segment pos1120" style="width: {(dist.get('pos_11_20', 0) / total_kw * 100) if total_kw else 0}%">
                    11-20: {dist.get('pos_11_20', 0)}
                </div>
                <div class="dist-segment pos21plus" style="width: {(dist.get('pos_21_plus', 0) / total_kw * 100) if total_kw else 0}%">
                    21+: {dist.get('pos_21_plus', 0)}
                </div>
            </div>
        </div>
        """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Audit Report — {website['name']}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-500: #6b7280;
            --gray-700: #374151;
            --gray-900: #111827;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: var(--gray-900); line-height: 1.6; background: var(--gray-50); }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        .header {{ background: linear-gradient(135deg, var(--primary), #1d4ed8); color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
        .header h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .header .meta {{ opacity: 0.9; font-size: 0.9rem; }}
        .section {{ background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 1.25rem; color: var(--gray-900); margin-bottom: 1rem; border-bottom: 2px solid var(--gray-100); padding-bottom: 0.5rem; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }}
        .kpi {{ background: var(--gray-50); padding: 1rem; border-radius: 8px; text-align: center; }}
        .kpi .value {{ font-size: 1.5rem; font-weight: 700; color: var(--primary); }}
        .kpi .label {{ font-size: 0.8rem; color: var(--gray-500); margin-top: 0.25rem; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--gray-200); }}
        th {{ background: var(--gray-50); font-weight: 600; color: var(--gray-700); }}
        tr:hover {{ background: var(--gray-50); }}
        .ranking-dist {{ margin-top: 1rem; }}
        .dist-bar {{ display: flex; height: 32px; border-radius: 8px; overflow: hidden; }}
        .dist-segment {{ display: flex; align-items: center; justify-content: center; color: white; font-size: 0.75rem; font-weight: 600; min-width: 60px; }}
        .top3 {{ background: var(--success); }}
        .pos410 {{ background: var(--primary); }}
        .pos1120 {{ background: var(--warning); }}
        .pos21plus {{ background: var(--danger); }}
        .footer {{ text-align: center; color: var(--gray-500); font-size: 0.8rem; margin-top: 2rem; }}
        @media print {{
            body {{ background: white; }}
            .container {{ padding: 0; }}
            .section {{ box-shadow: none; border: 1px solid var(--gray-200); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 SEO Audit Report</h1>
            <div class="meta">
                <strong>{website['name']}</strong> — {website['url']}<br>
                Period: Last {config.period_days} days | Generated: {generated_at}
            </div>
        </div>

        <div class="section">
            <h2>📈 Executive Summary</h2>
            <div class="kpi-grid">
                <div class="kpi">
                    <div class="value">{overview['total_clicks']:,}</div>
                    <div class="label">Total Clicks</div>
                </div>
                <div class="kpi">
                    <div class="value">{overview['total_impressions']:,}</div>
                    <div class="label">Total Impressions</div>
                </div>
                <div class="kpi">
                    <div class="value">{overview['avg_ctr']:.2%}</div>
                    <div class="label">Average CTR</div>
                </div>
                <div class="kpi">
                    <div class="value">{overview['avg_position']:.1f}</div>
                    <div class="label">Average Position</div>
                </div>
                <div class="kpi">
                    <div class="value">{overview['pages_indexed']:,}</div>
                    <div class="label">Pages Indexed</div>
                </div>
                <div class="kpi">
                    <div class="value">{overview['unique_queries']:,}</div>
                    <div class="label">Unique Queries</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Traffic Trend</h2>
            {trend_html}
        </div>

        <div class="section">
            <h2>🎯 Rankings Distribution</h2>
            {dist_html}
        </div>

        <div class="section">
            <h2>📄 Top Pages by Clicks</h2>
            {pages_html}
        </div>

        <div class="section">
            <h2>🔍 Top Queries by Impressions</h2>
            {queries_html}
        </div>

        <div class="section">
            <h2>⚠️ SEO Findings</h2>
            {findings_html}
        </div>

        <div class="footer">
            Generated by SEO Content Intelligence | {generated_at}
        </div>
    </div>
</body>
</html>"""
        return html

    def _render_traffic_chart(self, trend: list[dict]) -> str:
        if not trend:
            return '<p style="color: #6b7280; text-align: center;">No traffic data available for this period.</p>'

        max_clicks = max((d["clicks"] for d in trend), default=1) or 1
        bars = []
        for d in trend[-14:]:  # Last 14 days max
            pct = (d["clicks"] / max_clicks * 100) if max_clicks else 0
            bars.append(f'''
            <div style="flex:1; display:flex; flex-direction:column; align-items:center;">
                <div style="width:100%; background:var(--primary); height:{pct}%; min-height:2px; border-radius:4px 4px 0 0; opacity:0.8;"></div>
                <div style="font-size:0.65rem; color:var(--gray-500); margin-top:4px; transform:rotate(-45deg);">{d['date'][-5:]}</div>
                <div style="font-size:0.7rem; font-weight:600;">{d['clicks']}</div>
            </div>''')

        return f'<div style="display:flex; align-items:flex-end; gap:4px; height:160px; padding:1rem 0;">{"".join(bars)}</div>'

    def _render_findings_table(self, findings: list[dict]) -> str:
        if not findings:
            return '<p style="color: #6b7280;">No open SEO findings.</p>'

        rows = "\n".join(
            f'<tr><td>{f["severity"]}</td><td>{f["rec_type"]}</td><td>{f["count"]}</td></tr>'
            for f in findings
        )
        return f'''
        <table>
            <thead><tr><th>Severity</th><th>Type</th><th>Count</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>'''

    def _render_top_pages_table(self, pages: list[dict]) -> str:
        if not pages:
            return '<p style="color: #6b7280;">No page data available.</p>'

        rows = "\n".join(
            f'<tr><td title="{p["page_url"]}">{p["page_url"][:60]}{"..." if len(p["page_url"]) > 60 else ""}</td>'
            f'<td>{p["clicks"]:,}</td><td>{p["impressions"]:,}</td><td>{p["ctr"]:.2f}%</td><td>{p["position"]:.1f}</td></tr>'
            for p in pages
        )
        return f'''
        <table>
            <thead><tr><th>Page</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>'''

    def _render_top_queries_table(self, queries: list[dict]) -> str:
        if not queries:
            return '<p style="color: #6b7280;">No query data available.</p>'

        rows = "\n".join(
            f'<tr><td>{q["query"]}</td><td>{q["clicks"]:,}</td><td>{q["impressions"]:,}</td><td>{q["ctr"]:.2f}%</td><td>{q["position"]:.1f}</td></tr>'
            for q in queries
        )
        return f'''
        <table>
            <thead><tr><th>Query</th><th>Clicks</th><th>Impressions</th><th>CTR</th><th>Position</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>'''

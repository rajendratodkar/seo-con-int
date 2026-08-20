"""Single aggregation point for all routers. Business logic never lives here."""
from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.modules.article_planner.router import router as article_planner_router
from app.modules.ab_testing.router import router as ab_testing_router
from app.modules.competitor_analysis.router import router as competitor_analysis_router
from app.modules.keyword_clustering.router import router as keyword_clustering_router
from app.modules.schema_markup.router import router as schema_markup_router
from app.modules.content_calendar.router import router as content_calendar_router
from app.modules.backlink_monitor.router import router as backlink_monitor_router
from app.modules.page_speed.router import router as page_speed_router
from app.modules.content_rewriter.router import router as content_rewriter_router
from app.modules.seo_checklist.router import router as seo_checklist_router
from app.modules.sitemap_generator.router import router as sitemap_generator_router
from app.modules.report_generator.router import router as report_generator_router
from app.modules.serp_preview.router import router as serp_preview_router
from app.modules.redirect_manager.router import router as redirect_manager_router
from app.modules.rank_tracker.router import router as rank_tracker_router
from app.modules.serp_ab_testing.router import router as serp_ab_testing_router
from app.modules.content_brief.router import router as content_brief_router
from app.modules.content_refresh.router import router as content_refresh_router
from app.modules.bulk_operations.router import router as bulk_operations_router
from app.modules.monitoring.router import router as monitoring_router
from app.modules.content.router import router as content_router
from app.modules.content_audit.router import router as content_audit_router
from app.modules.content_ideas.router import router as content_ideas_router
from app.modules.diagnostics.router import router as diagnostics_router
from app.modules.discussion.router import router as discussion_router
from app.modules.google_analytics.router import router as google_analytics_router
from app.modules.internal_links.router import router as internal_links_router
from app.modules.keywords.router import router as keywords_router
from app.modules.pages.router import router as pages_router
from app.modules.publishing.router import router as publishing_router
from app.modules.references.router import router as references_router
from app.modules.reports.router import router as reports_router
from app.modules.research.router import router as research_router
from app.modules.search_console.router import router as search_console_router
from app.modules.seo_analysis.router import analysis_router, findings_router
from app.modules.seo_opportunities.router import router as opportunities_router
from app.modules.settings.router import router as settings_router
from app.modules.topic_clusters.router import router as topic_clusters_router
from app.modules.websites.router import router as websites_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(websites_router, prefix="/websites", tags=["websites"])
api_router.include_router(pages_router, prefix="/pages", tags=["pages"])
api_router.include_router(search_console_router, prefix="/search-console", tags=["search-console"])
api_router.include_router(google_analytics_router, prefix="/google-analytics", tags=["google-analytics"])
api_router.include_router(analysis_router, prefix="/seo/analysis", tags=["seo-analysis"])
api_router.include_router(findings_router, prefix="/findings", tags=["findings"])
api_router.include_router(opportunities_router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(references_router, prefix="/references", tags=["references"])
api_router.include_router(content_audit_router, prefix="/content-audit", tags=["content-audit"])
api_router.include_router(research_router, prefix="/research", tags=["research"])
api_router.include_router(content_ideas_router, prefix="/content-ideas", tags=["content-ideas"])
api_router.include_router(keywords_router, prefix="/keywords", tags=["keywords"])
api_router.include_router(discussion_router, prefix="/discussions", tags=["discussions"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(article_planner_router, prefix="/article-plans", tags=["article-plans"])
api_router.include_router(content_router, prefix="/content", tags=["content"])
api_router.include_router(publishing_router, prefix="/publishing", tags=["publishing"])
api_router.include_router(topic_clusters_router, prefix="/topic-clusters", tags=["topic-clusters"])
api_router.include_router(internal_links_router, prefix="/internal-links", tags=["internal-links"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(diagnostics_router, prefix="/diagnostics", tags=["diagnostics"])
api_router.include_router(bulk_operations_router, prefix="/bulk", tags=["bulk-operations"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(ab_testing_router, prefix="/ab-tests", tags=["ab-testing"])
api_router.include_router(competitor_analysis_router, prefix="/competitors", tags=["competitor-analysis"])
api_router.include_router(keyword_clustering_router, prefix="/keyword-clusters", tags=["keyword-clustering"])
api_router.include_router(schema_markup_router, prefix="/schemas", tags=["schema-markup"])
api_router.include_router(content_calendar_router, prefix="/calendar", tags=["content-calendar"])
api_router.include_router(backlink_monitor_router, prefix="/backlinks", tags=["backlink-monitor"])
api_router.include_router(page_speed_router, prefix="/page-speed", tags=["page-speed"])
api_router.include_router(content_rewriter_router, prefix="/rewriter", tags=["content-rewriter"])
api_router.include_router(seo_checklist_router, prefix="/seo-checklist", tags=["seo-checklist"])
api_router.include_router(sitemap_generator_router, prefix="/sitemap-gen", tags=["sitemap-generator"])
api_router.include_router(report_generator_router, prefix="/reports/generate", tags=["report-generator"])
api_router.include_router(serp_preview_router, prefix="/serp-preview", tags=["serp-preview"])
api_router.include_router(redirect_manager_router, prefix="/redirects", tags=["redirect-manager"])
api_router.include_router(rank_tracker_router, prefix="/rank-tracker", tags=["rank-tracker"])
api_router.include_router(serp_ab_testing_router, prefix="/serp-ab-tests", tags=["serp-ab-testing"])
api_router.include_router(content_brief_router, prefix="/content-briefs", tags=["content-briefs"])
api_router.include_router(content_refresh_router, prefix="/content-refresh", tags=["content-refresh"])

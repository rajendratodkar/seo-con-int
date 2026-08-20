"""Reports HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.reports.service import ReportsService

router = APIRouter()


@router.get("/weekly")
def weekly(db: DbSession, website_id: int = Query(...)):
    return ReportsService(db).weekly(website_id)


@router.get("/analytics/overview")
def analytics_overview(
    db: DbSession,
    website_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
):
    """Rich analytics: KPIs, traffic trend, top pages, top queries, findings breakdown."""
    return ReportsService(db).analytics_overview(website_id, days)


@router.get("/analytics/traffic-trend")
def traffic_trend(
    db: DbSession,
    website_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
):
    """Daily traffic trend (clicks + impressions over time)."""
    return ReportsService(db).traffic_trend(website_id, days)


@router.get("/analytics/ranking-distribution")
def ranking_distribution(
    db: DbSession,
    website_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
):
    """How our keywords distribute across position buckets."""
    return ReportsService(db).ranking_distribution(website_id, days)


@router.get("/analytics/top-pages")
def top_pages(
    db: DbSession,
    website_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """Top pages by clicks with impressions, CTR, and position."""
    return ReportsService(db).top_pages(website_id, days, limit)


@router.get("/analytics/top-queries")
def top_queries(
    db: DbSession,
    website_id: int = Query(...),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
):
    """Top queries by impressions with clicks, CTR, and position."""
    return ReportsService(db).top_queries(website_id, days, limit)

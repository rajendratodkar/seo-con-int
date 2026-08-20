"""Keyword Clustering HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.keyword_clustering.schemas import (
    AutoClusterRequest,
    ClusterCreate,
    ClusterKeywordAdd,
    ClusterUpdate,
)
from app.modules.keyword_clustering.service import KeywordClusterService

router = APIRouter()


def _svc(db: DbSession) -> KeywordClusterService:
    return KeywordClusterService(db)


# ===========================================================================
# Clusters
# ===========================================================================

@router.post("", status_code=201)
def create_cluster(payload: ClusterCreate, db: DbSession):
    """Create a keyword cluster."""
    return _svc(db).create_cluster(
        payload.website_id, payload.name, payload.description, payload.pillar_keyword,
    )


@router.get("")
def list_clusters(db: DbSession, website_id: int = Query(...)):
    """List all keyword clusters for a website."""
    return _svc(db).list_clusters(website_id)


@router.get("/{cluster_id}")
def get_cluster(cluster_id: int, db: DbSession):
    """Get cluster detail with all keywords."""
    return _svc(db).get_cluster_detail(cluster_id)


@router.patch("/{cluster_id}")
def update_cluster(cluster_id: int, payload: ClusterUpdate, db: DbSession):
    """Update a cluster."""
    return _svc(db).update_cluster(
        cluster_id, name=payload.name, description=payload.description, pillar_keyword=payload.pillar_keyword,
    )


@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: DbSession):
    """Delete a cluster and all its keywords."""
    return _svc(db).delete_cluster(cluster_id)


# ===========================================================================
# Keywords in clusters
# ===========================================================================

@router.post("/{cluster_id}/keywords", status_code=201)
def add_keywords(cluster_id: int, keywords: list[ClusterKeywordAdd], db: DbSession):
    """Add keywords to a cluster."""
    return _svc(db).add_keywords(cluster_id, [k.model_dump() for k in keywords])


@router.get("/{cluster_id}/keywords")
def list_keywords(cluster_id: int, db: DbSession):
    """List keywords in a cluster."""
    return _svc(db).get_cluster_detail(cluster_id)["keywords"]


@router.delete("/keywords/{item_id}")
def remove_keyword(item_id: int, db: DbSession):
    """Remove a keyword from a cluster."""
    return _svc(db).remove_keyword(item_id)


@router.post("/{cluster_id}/import")
def import_from_keywords(cluster_id: int, db: DbSession, website_id: int = Query(...)):
    """Import keywords from the main keywords table into a cluster."""
    return _svc(db).import_from_keywords(website_id, cluster_id)


# ===========================================================================
# Auto-clustering
# ===========================================================================

@router.post("/auto")
def auto_cluster(payload: AutoClusterRequest, db: DbSession):
    """Automatically cluster keywords from Search Console data."""
    return _svc(db).auto_cluster(
        payload.website_id, payload.min_keywords_per_cluster, payload.similarity_threshold,
    )

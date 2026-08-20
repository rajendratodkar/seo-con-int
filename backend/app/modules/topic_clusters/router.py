"""Topic clusters HTTP layer."""
from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.core.exceptions import NotFoundError
from app.modules.topic_clusters.service import TopicClustersService

router = APIRouter()


@router.post("/auto")
def auto_cluster(db: DbSession, website_id: int = Query(...)):
    items = TopicClustersService(db).auto_cluster(website_id)
    return {"items": items, "total": len(items)}


@router.get("/")
def list_clusters(db: DbSession, website_id: int = Query(...)):
    items = TopicClustersService(db).list(website_id)
    return {"items": items, "total": len(items)}


@router.get("/{cluster_id}")
def get_cluster(db: DbSession, cluster_id: int):
    return TopicClustersService(db).get(cluster_id)


@router.delete("/{cluster_id}")
def delete_cluster(db: DbSession, cluster_id: int):
    if not TopicClustersService(db).delete(cluster_id):
        raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} does not exist")
    return {"deleted": cluster_id}

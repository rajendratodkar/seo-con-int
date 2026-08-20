"""Keyword Clustering service — manage clusters, auto-cluster, import keywords."""
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.keyword_clustering.engine import cluster_keywords
from app.modules.keyword_clustering.repository import KeywordClusterRepository

logger = logging.getLogger(__name__)


class KeywordClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = KeywordClusterRepository(db)
        self.repo.ensure_table()

    def create_cluster(self, website_id: int, name: str, description: str | None, pillar_keyword: str | None) -> dict:
        return self.repo.create_cluster(website_id, name, description, pillar_keyword)

    def list_clusters(self, website_id: int) -> list[dict]:
        clusters = self.repo.list_clusters(website_id)
        # Add keyword count to each cluster
        for c in clusters:
            c["keyword_count"] = self.repo.get_keyword_count(c["id"])
        return clusters

    def get_cluster_detail(self, cluster_id: int) -> dict:
        c = self.repo.get_cluster(cluster_id)
        if not c:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} not found")
        keywords = self.repo.list_keywords(cluster_id)
        return {**c, "keywords": keywords, "keyword_count": len(keywords)}

    def update_cluster(self, cluster_id: int, **fields) -> dict:
        c = self.repo.update_cluster(cluster_id, **fields)
        if not c:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} not found")
        return c

    def delete_cluster(self, cluster_id: int) -> dict:
        c = self.repo.get_cluster(cluster_id)
        if not c:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} not found")
        self.repo.delete_cluster(cluster_id)
        return {"deleted": True, "id": cluster_id}

    def add_keywords(self, cluster_id: int, keywords: list[dict]) -> dict:
        c = self.repo.get_cluster(cluster_id)
        if not c:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} not found")
        count = self.repo.bulk_add_keywords(cluster_id, keywords)
        return {"added": count, "cluster_id": cluster_id}

    def remove_keyword(self, item_id: int) -> dict:
        if not self.repo.remove_keyword(item_id):
            raise NotFoundError("keyword.not_found", f"Keyword item {item_id} not found")
        return {"deleted": True, "id": item_id}

    def import_from_keywords(self, website_id: int, cluster_id: int) -> dict:
        c = self.repo.get_cluster(cluster_id)
        if not c:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} not found")
        count = self.repo.import_from_keywords(website_id, cluster_id)
        return {"imported": count, "cluster_id": cluster_id}

    def auto_cluster(
        self, website_id: int,
        min_keywords_per_cluster: int = 2,
        similarity_threshold: float = 0.3,
    ) -> dict:
        """Automatically cluster keywords from Search Console data."""
        keywords = self.repo.get_website_keywords(website_id)
        if not keywords:
            return {"clusters_created": 0, "keywords_processed": 0, "message": "No keywords found"}

        # Run the clustering engine
        raw_clusters = cluster_keywords(keywords, similarity_threshold, min_keywords_per_cluster)

        # Create clusters and add keywords
        clusters_created = 0
        keywords_clustered = 0
        for rc in raw_clusters:
            cluster = self.repo.create_cluster(
                website_id, f"Auto: {rc['name']}", f"Auto-generated from {len(rc['keywords'])} keywords",
                pillar_keyword=rc["keywords"][0] if rc["keywords"] else None,
            )
            for kw in rc["keywords"]:
                try:
                    self.repo.add_keyword(cluster["id"], kw, source="auto_cluster")
                    keywords_clustered += 1
                except Exception:
                    pass
            clusters_created += 1

        return {
            "clusters_created": clusters_created,
            "keywords_processed": len(keywords),
            "keywords_clustered": keywords_clustered,
        }

"""Topic clusters: group pages into pillar/support structures (deterministic).

Clustering is data-based: pages are grouped by their first URL path segment;
keyword groups from `keywords.group_name` refine the naming. No AI involved.
"""
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError


class TopicClustersService:
    def __init__(self, db: Session):
        self.db = db

    def auto_cluster(self, website_id: int) -> list[dict]:
        pages = self.db.execute(
            text("SELECT id, url, title FROM pages WHERE website_id = :w AND status_code < 400"),
            {"w": website_id},
        ).mappings().all()

        # Group pages by first URL path segment
        groups: dict[str, list[dict]] = {}
        for page in pages:
            segment = urlparse(page["url"]).path.strip("/").split("/")[0] or "home"
            groups.setdefault(segment, []).append(dict(page))

        created = []
        for segment, members in groups.items():
            if len(members) < 2:
                continue  # single page = no cluster
            cluster_id = self._get_or_create(website_id, segment.replace("-", " ").title(), members)
            created.append(self.get(cluster_id))
        return created

    def _get_or_create(self, website_id: int, name: str, members: list[dict]) -> int:
        row = self.db.execute(
            text("SELECT id FROM topic_clusters WHERE website_id = :w AND name = :n"),
            {"w": website_id, "n": name},
        ).first()
        if row:
            cluster_id = row[0]
        else:
            # Pillar = shortest URL in the group
            pillar = min(members, key=lambda m: len(m["url"]))
            result = self.db.execute(
                text(
                    "INSERT INTO topic_clusters (website_id, name, description, pillar_page_id) "
                    "VALUES (:w, :n, :d, :p)"
                ),
                {"w": website_id, "n": name, "d": f"Auto-clustered from URL path segment.", "p": pillar["id"]},
            )
            cluster_id = result.lastrowid
        for member in members:
            self.db.execute(
                text(
                    "INSERT OR IGNORE INTO topic_cluster_pages (cluster_id, page_id) VALUES (:c, :p)"
                ),
                {"c": cluster_id, "p": member["id"]},
            )
        self.db.commit()
        return cluster_id

    def list(self, website_id: int) -> list[dict]:
        rows = self.db.execute(
            text("SELECT * FROM topic_clusters WHERE website_id = :w ORDER BY id"), {"w": website_id}
        ).mappings().all()
        clusters = []
        for row in rows:
            cluster = dict(row)
            cluster["pages"] = [
                dict(p) for p in self.db.execute(
                    text(
                        "SELECT p.id, p.url, p.title FROM topic_cluster_pages tcp "
                        "JOIN pages p ON p.id = tcp.page_id WHERE tcp.cluster_id = :c"
                    ),
                    {"c": cluster["id"]},
                ).mappings().all()
            ]
            clusters.append(cluster)
        return clusters

    def get(self, cluster_id: int) -> dict:
        row = self.db.execute(
            text("SELECT * FROM topic_clusters WHERE id = :id"), {"id": cluster_id}
        ).mappings().first()
        if row is None:
            raise NotFoundError("cluster.not_found", f"Cluster {cluster_id} does not exist")
        cluster = dict(row)
        cluster["pages"] = [
            dict(p) for p in self.db.execute(
                text(
                    "SELECT p.id, p.url, p.title FROM topic_cluster_pages tcp "
                    "JOIN pages p ON p.id = tcp.page_id WHERE tcp.cluster_id = :c"
                ),
                {"c": cluster_id},
            ).mappings().all()
        ]
        return cluster

    def delete(self, cluster_id: int) -> bool:
        result = self.db.execute(text("DELETE FROM topic_clusters WHERE id = :id"), {"id": cluster_id})
        self.db.commit()
        return result.rowcount > 0

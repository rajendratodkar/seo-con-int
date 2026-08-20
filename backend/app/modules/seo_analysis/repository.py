"""Findings persistence — the Recommendation object lives in seo_findings (plan §16)."""
import json

from sqlalchemy import text
from sqlalchemy.orm import Session


class FindingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def rule_lookup(self) -> dict:
        rows = self.db.execute(text("SELECT id, rule_code, reference_id FROM seo_rules")).fetchall()
        return {row.rule_code: {"id": row.id, "reference_id": row.reference_id} for row in rows}

    def replace_page_findings(self, website_id: int, page_id: int, rule_findings: list[dict], rules: dict) -> int:
        """Replace unresolved open findings for a page, insert fresh ones."""
        self.db.execute(
            text(
                "DELETE FROM seo_findings WHERE page_id = :page_id AND status = 'open' "
                "AND rec_type IN ('rule_based', 'data_based')"
            ),
            {"page_id": page_id},
        )
        saved = 0
        for finding in rule_findings:
            rule = rules.get(finding.get("rule_code"), {})
            self.db.execute(
                text(
                    "INSERT INTO seo_findings "
                    "(website_id, page_id, rule_id, recommendation, why, evidence, data, reference_id, "
                    "confidence, severity, rec_type, status) "
                    "VALUES (:website_id, :page_id, :rule_id, :recommendation, :why, :evidence, :data, "
                    ":reference_id, :confidence, :severity, :rec_type, 'open')"
                ),
                {
                    "website_id": website_id,
                    "page_id": page_id,
                    "rule_id": rule.get("id"),
                    "recommendation": finding["recommendation"],
                    "why": finding["why"],
                    "evidence": finding["evidence"],
                    "data": json.dumps(finding.get("data", {}), ensure_ascii=False),
                    "reference_id": rule.get("reference_id"),
                    "confidence": finding.get("confidence", "medium"),
                    "severity": finding.get("severity", "info"),
                    "rec_type": finding.get("rec_type", "rule_based"),
                },
            )
            saved += 1
        return saved

    def save_opportunity(self, website_id: int, page_id: int | None, finding: dict) -> None:
        # Avoid duplicating an identical open opportunity for the same page
        existing = self.db.execute(
            text(
                "SELECT id FROM seo_findings WHERE website_id = :website_id AND page_id IS :page_id "
                "AND rec_type = 'data_based' AND status = 'open' AND recommendation = :recommendation"
            ),
            {"website_id": website_id, "page_id": page_id, "recommendation": finding["recommendation"]},
        ).first()
        if existing:
            self.db.execute(
                text("UPDATE seo_findings SET evidence=:evidence, data=:data, updated_at=datetime('now') WHERE id=:id"),
                {"evidence": finding["evidence"], "data": json.dumps(finding["data"], ensure_ascii=False), "id": existing.id},
            )
            return
        self.db.execute(
            text(
                "INSERT INTO seo_findings "
                "(website_id, page_id, recommendation, why, evidence, data, confidence, severity, rec_type, status) "
                "VALUES (:website_id, :page_id, :recommendation, :why, :evidence, :data, "
                ":confidence, :severity, 'data_based', 'open')"
            ),
            {
                "website_id": website_id,
                "page_id": page_id,
                "recommendation": finding["recommendation"],
                "why": finding["why"],
                "evidence": finding["evidence"],
                "data": json.dumps(finding["data"], ensure_ascii=False),
                "confidence": finding["confidence"],
                "severity": finding["severity"],
            },
        )

    def list(self, website_id: int | None, rec_type: str | None, status: str | None, offset: int, limit: int):
        clauses, params = [], {"limit": limit, "offset": offset}
        if website_id:
            clauses.append("f.website_id = :website_id")
            params["website_id"] = website_id
        if rec_type:
            clauses.append("f.rec_type = :rec_type")
            params["rec_type"] = rec_type
        if status:
            clauses.append("f.status = :status")
            params["status"] = status
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.execute(
            text(
                f"SELECT f.*, r.rule_code, r.name AS rule_name, rd.title AS reference_title "
                f"FROM seo_findings f "
                f"LEFT JOIN seo_rules r ON r.id = f.rule_id "
                f"LEFT JOIN reference_docs rd ON rd.id = f.reference_id "
                f"{where} ORDER BY f.id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).mappings().all()
        total = self.db.execute(text(f"SELECT COUNT(*) FROM seo_findings f {where}"), params).scalar_one()
        return [dict(r) for r in rows], total

    def get(self, finding_id: int) -> dict | None:
        row = self.db.execute(
            text(
                "SELECT f.*, r.rule_code, r.name AS rule_name, rd.title AS reference_title, rd.url AS reference_url "
                "FROM seo_findings f "
                "LEFT JOIN seo_rules r ON r.id = f.rule_id "
                "LEFT JOIN reference_docs rd ON rd.id = f.reference_id WHERE f.id = :id"
            ),
            {"id": finding_id},
        ).mappings().first()
        return dict(row) if row else None

    def set_status(self, finding_id: int, status: str) -> None:
        self.db.execute(
            text("UPDATE seo_findings SET status=:status, updated_at=datetime('now') WHERE id=:id"),
            {"status": status, "id": finding_id},
        )

    def add_action(self, finding_id: int, action: str) -> int:
        result = self.db.execute(
            text("INSERT INTO seo_actions (finding_id, action) VALUES (:finding_id, :action)"),
            {"finding_id": finding_id, "action": action},
        )
        return result.lastrowid

"""Content Brief service — orchestrates analysis engines and brief generation."""
import json
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.content_brief.repository import ContentBriefRepository
from app.engines.brief.serp_analyzer import detect_serp_features
from app.engines.brief.competitor_analyzer import analyze_competitors
from app.engines.brief.structure_recommender import recommend_structure


class ContentBriefService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContentBriefRepository(self.db)

    def generate(self, website_id: int, target_keyword: str) -> dict:
        """Generate a content brief by running all analysis engines."""
        primary_keyword = target_keyword
        keyword = target_keyword.strip()

        # 1. Create brief record
        brief = self.repo.create(website_id, keyword, primary_keyword)

        # 2. SERP analysis
        serp_data = detect_serp_features(self.db, website_id, keyword)

        # 3. Competitor analysis
        competitors = analyze_competitors(self.db, website_id, keyword)

        # 4. Structure recommendation
        structure = recommend_structure(competitors, serp_data, keyword)

        # 5. Build brief output
        title_options = self._generate_title_options(keyword, serp_data)
        meta_descriptions = self._generate_meta_options(keyword, serp_data)
        faq = self._extract_faq_suggestions(serp_data)
        key_talking_points = self._extract_talking_points(serp_data, competitors)

        # Source evidence
        source_evidence = {
            "serp_data": {
                "query_volume": serp_data.get("query_volume", 0),
                "avg_position": serp_data.get("avg_position", 0),
                "dominant_intent": serp_data.get("dominant_intent", "unknown"),
                "features_count": len(serp_data.get("features_detected", [])),
            },
            "competitor_count": len(competitors),
            "has_search_console_data": serp_data.get("query_volume", 0) > 0,
        }

        # 6. Update brief with all data
        brief = self.repo.update(brief["id"], {
            "primary_keyword": primary_keyword,
            "secondary_keywords": self._extract_secondary_keywords(serp_data, keyword),
            "search_intent": serp_data.get("dominant_intent", "informational"),
            "target_word_count": structure.get("target_word_count", 2000),
            "title_options": title_options,
            "meta_descriptions": meta_descriptions,
            "outline": structure.get("outline", []),
            "faq": faq,
            "things_to_avoid": structure.get("things_to_avoid", []),
            "key_talking_points": key_talking_points,
            "serp_features": serp_data,
            "internal_links": structure.get("internal_link_anchors", []),
            "source_evidence": source_evidence,
        })

        # 7. Store competitor data
        for comp in competitors:
            self.repo.add_competitor(brief["id"], comp)

        # 8. Store analysis sections
        self.repo.add_section(brief["id"], "serp_feature", "SERP Features Analysis",
                              json.dumps(serp_data.get("features_detected", [])), 0)
        self.repo.add_section(brief["id"], "competitor_insight", "Competitor Analysis",
                              json.dumps(structure.get("competitor_stats", {})), 1)
        self.repo.add_section(brief["id"], "keyword_data", "Keyword Data",
                              json.dumps({"intent": serp_data.get("dominant_intent"), "volume": serp_data.get("query_volume")}), 2)

        # 9. Generate markdown export
        markdown = self._render_markdown(brief)
        self.repo.update(brief["id"], {"markdown_export": markdown})

        return self.repo.get(brief["id"]) or brief

    def get(self, brief_id: int) -> dict:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return brief

    def list_by_website(self, website_id: int) -> list[dict]:
        return self.repo.list_by_website(website_id)

    def update(self, brief_id: int, fields: dict) -> dict:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return self.repo.update(brief_id, fields)

    def delete(self, brief_id: int) -> bool:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return self.repo.delete(brief_id)

    def get_sections(self, brief_id: int) -> list[dict]:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return self.repo.get_sections(brief_id)

    def get_competitors(self, brief_id: int) -> list[dict]:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return self.repo.get_competitors(brief_id)

    def export_markdown(self, brief_id: int) -> str:
        brief = self.repo.get(brief_id)
        if not brief:
            raise NotFoundError("brief.not_found", f"Content brief {brief_id} not found")
        return self._render_markdown(brief)

    def finalize(self, brief_id: int) -> dict:
        """Mark brief as finalized."""
        return self.repo.update(brief_id, {"status": "finalized"})

    def send_to_planner(self, brief_id: int) -> dict:
        """Mark brief as sent to article planner."""
        return self.repo.update(brief_id, {"status": "sent_to_planner" })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _generate_title_options(self, keyword: str, serp_data: dict) -> list[str]:
        """Generate title suggestions based on keyword and SERP data."""
        intent = serp_data.get("dominant_intent", "informational")
        titles = [
            f"The Complete Guide to {keyword.title()}",
            f"{keyword.title()}: Everything You Need to Know",
            f"What Is {keyword.title()}? A Detailed Explanation",
        ]
        if intent == "commercial":
            titles.append(f"Best {keyword.title()} Options Compared ({2026})")
        if intent == "transactional":
            titles.append(f"How to Get Started with {keyword.title()}")
        if intent == "informational":
            titles.append(f"Understanding {keyword.title()}: A Beginner's Guide")
        return titles

    def _generate_meta_options(self, keyword: str, serp_data: dict) -> list[str]:
        """Generate meta description suggestions (120-155 chars)."""
        return [
            f"Learn everything about {keyword} in this comprehensive guide. Tips, examples, and expert insights included.",
            f"Discover what {keyword} is, how it works, and why it matters. Complete guide with practical examples.",
            f"Looking for information on {keyword}? Our detailed guide covers benefits, best practices, and FAQs.",
        ]

    def _extract_secondary_keywords(self, serp_data: dict, keyword: str) -> list[str]:
        """Extract secondary keywords from related SC queries."""
        secondary = []
        for q in serp_data.get("queries", []):
            query = q.get("query", "").lower()
            if query != keyword.lower() and query not in secondary:
                secondary.append(query)
            if len(secondary) >= 10:
                break
        return secondary

    def _extract_faq_suggestions(self, serp_data: dict) -> list[dict]:
        """Extract FAQ suggestions from PAA queries."""
        faq = []
        for feature in serp_data.get("features_detected", []):
            if feature["type"] == "people_also_ask":
                for question in feature.get("sample_questions", []):
                    faq.append({
                        "question": question,
                        "answer": "",  # To be filled by AI or manually
                    })
        # Add common FAQ templates if no PAA detected
        if not faq:
            keyword = serp_data.get("queries", [{}])[0].get("query", "this topic") if serp_data.get("queries") else "this topic"
            faq = [
                {"question": f"What is {keyword}?", "answer": ""},
                {"question": f"Why is {keyword} important?", "answer": ""},
                {"question": f"How do I get started with {keyword}?", "answer": ""},
            ]
        return faq

    def _extract_talking_points(self, serp_data: dict, competitors: list[dict]) -> list[str]:
        """Extract key talking points from analysis."""
        points = []

        # From SERP features
        for feature in serp_data.get("features_detected", []):
            if feature["type"] == "featured_snippet":
                points.append("Optimize for featured snippet with concise, direct answers")
            elif feature["type"] == "people_also_ask":
                points.append("Address common questions to capture PAA snippets")

        # From competitor gaps
        if competitors:
            no_faq = sum(1 for c in competitors if not c.get("has_faq"))
            if no_faq > len(competitors) * 0.5:
                points.append("Add FAQ section — most competitors lack one")
            no_schema = sum(1 for c in competitors if not c.get("has_schema"))
            if no_schema > len(competitors) * 0.5:
                points.append("Add structured data (FAQ/Article schema) — competitors lack it")

        points.append("Include original data, examples, or case studies to differentiate")
        points.append("Use clear headings and short paragraphs for readability")

        return points

    def _render_markdown(self, brief: dict) -> str:
        """Render the brief as a structured Markdown document."""
        lines = []
        lines.append(f"# Content Brief: {brief.get('target_keyword', '')}")
        lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **Target Keyword:** {brief.get('target_keyword', '')}")
        lines.append(f"- **Primary Keyword:** {brief.get('primary_keyword', '')}")
        if brief.get("secondary_keywords"):
            kw_list = brief["secondary_keywords"]
            if isinstance(kw_list, str):
                kw_list = json.loads(kw_list)
            lines.append(f"- **Secondary Keywords:** {', '.join(kw_list)}")
        lines.append(f"- **Search Intent:** {brief.get('search_intent', 'N/A')}")
        lines.append(f"- **Target Word Count:** {brief.get('target_word_count', 'N/A')}")
        lines.append("")

        # Title Options
        titles = brief.get("title_options", [])
        if isinstance(titles, str):
            titles = json.loads(titles)
        if titles:
            lines.append("## Title Options")
            for i, t in enumerate(titles, 1):
                lines.append(f"{i}. {t}")
            lines.append("")

        # Meta Descriptions
        metas = brief.get("meta_descriptions", [])
        if isinstance(metas, str):
            metas = json.loads(metas)
        if metas:
            lines.append("## Meta Description Options")
            for i, m in enumerate(metas, 1):
                lines.append(f"{i}. {m}")
            lines.append("")

        # Outline
        outline = brief.get("outline", [])
        if isinstance(outline, str):
            outline = json.loads(outline)
        if outline:
            lines.append("## Outline")
            for item in outline:
                level = item.get("level", 2)
                prefix = "#" * level
                lines.append(f"{prefix} {item.get('heading', '')}")
                if item.get("notes"):
                    lines.append(f"  _{item['notes']}_")
            lines.append("")

        # Key Talking Points
        points = brief.get("key_talking_points", [])
        if isinstance(points, str):
            points = json.loads(points)
        if points:
            lines.append("## Key Talking Points")
            for p in points:
                lines.append(f"- {p}")
            lines.append("")

        # FAQ
        faq = brief.get("faq", [])
        if isinstance(faq, str):
            faq = json.loads(faq)
        if faq:
            lines.append("## FAQ")
            for item in faq:
                lines.append(f"**Q: {item.get('question', '')}**")
                if item.get("answer"):
                    lines.append(f"A: {item['answer']}")
                lines.append("")

        # Things to Avoid
        avoid = brief.get("things_to_avoid", [])
        if isinstance(avoid, str):
            avoid = json.loads(avoid)
        if avoid:
            lines.append("## Things to Avoid")
            for a in avoid:
                lines.append(f"- {a}")
            lines.append("")

        return "\n".join(lines)

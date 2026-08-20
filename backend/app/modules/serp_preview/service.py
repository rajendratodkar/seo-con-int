"""SERP Preview service — generates Google-style search result previews with scoring."""
import re
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.serp_preview.repository import SERPPreviewRepository
from app.modules.serp_preview.schemas import SERPPreviewRequest


class SERPPreviewService:
    # Google SERP limits
    TITLE_MAX_CHARS = 60
    TITLE_WARN_CHARS = 50
    DESCRIPTION_MAX_CHARS = 160
    DESCRIPTION_WARN_CHARS = 120
    DESCRIPTION_MIN_CHARS = 70

    def __init__(self, db: Session):
        self.db = db
        self.repo = SERPPreviewRepository(db)

    def generate_preview(self, data: SERPPreviewRequest) -> dict:
        """Generate a SERP preview from provided data."""
        # Process title
        title = data.title.strip()
        truncated_title = self._truncate_title(title)
        title_status = self._get_title_status(title)

        # Process description
        description = data.description.strip()
        truncated_description = self._truncate_description(description)
        description_status = self._get_description_status(description)

        # Process URL
        display_url = self._format_display_url(data.url)

        # Calculate score
        score_result = self._calculate_score(title, description, data.url)

        return {
            "title": title,
            "truncated_title": truncated_title,
            "title_length": len(title),
            "title_status": title_status,
            "description": description,
            "truncated_description": truncated_description,
            "description_length": len(description),
            "description_status": description_status,
            "url": data.url,
            "display_url": display_url,
            "site_name": data.site_name,
            "date": data.date,
            "score": score_result["score"],
            "score_breakdown": score_result["breakdown"],
            "tips": score_result["tips"],
        }

    def preview_from_page(self, page_id: int) -> dict:
        """Generate SERP preview for an existing page."""
        page = self.repo.get_page_meta(page_id)
        if not page:
            raise NotFoundError("page.not_found", f"Page {page_id} not found")

        title = page.get("title") or "Untitled Page"
        description = page.get("meta_description") or "No meta description set"

        return self.generate_preview(SERPPreviewRequest(
            title=title,
            description=description,
            url=page["url"],
        ))

    def bulk_preview(self, website_id: int, limit: int = 50) -> list[dict]:
        """Generate SERP previews for all pages in a website."""
        website = self.repo.get_website_info(website_id)
        if not website:
            raise NotFoundError("website.not_found", f"Website {website_id} not found")

        pages = self.repo.get_pages_for_website(website_id, limit)
        previews = []

        for page in pages:
            title = page.get("title") or "Untitled Page"
            description = page.get("meta_description") or "No meta description set"

            preview = self.generate_preview(SERPPreviewRequest(
                title=title,
                description=description,
                url=page["url"],
                site_name=website["name"],
            ))
            preview["page_id"] = page["id"]
            previews.append(preview)

        return previews

    def bulk_score(self, website_id: int, limit: int = 200) -> dict:
        """Score all pages in a website and return summary with details."""
        website = self.repo.get_website_info(website_id)
        if not website:
            raise NotFoundError("website.not_found", f"Website {website_id} not found")

        pages = self.repo.get_pages_for_website(website_id, limit)
        scored_pages = []

        for page in pages:
            title = page.get("title") or "Untitled Page"
            description = page.get("meta_description") or "No meta description set"

            # Calculate score without full preview (lightweight)
            score_result = self._calculate_score(title, description, page["url"])

            scored_pages.append({
                "page_id": page["id"],
                "url": page["url"],
                "title": title,
                "title_length": len(title),
                "description": description,
                "description_length": len(description),
                "score": score_result["score"],
                "title_score": score_result["breakdown"]["title"]["score"],
                "description_score": score_result["breakdown"]["description"]["score"],
                "url_score": score_result["breakdown"]["url"]["score"],
                "top_issues": [t for t in score_result["tips"] if t["type"] in ("error", "warning")][:3],
            })

        # Sort by score ascending (worst first)
        scored_pages.sort(key=lambda x: x["score"])

        # Calculate summary stats
        scores = [p["score"] for p in scored_pages]
        avg_score = sum(scores) / len(scores) if scores else 0

        excellent = sum(1 for s in scores if s >= 85)
        good = sum(1 for s in scores if 70 <= s < 85)
        moderate = sum(1 for s in scores if 50 <= s < 70)
        poor = sum(1 for s in scores if s < 50)

        # Common issues
        all_issues = {}
        for page in scored_pages:
            for issue in page["top_issues"]:
                key = issue["text"][:50]
                all_issues[key] = all_issues.get(key, 0) + 1
        common_issues = sorted(all_issues.items(), key=lambda x: -x[1])[:10]

        return {
            "website": website["name"],
            "total_pages": len(scored_pages),
            "avg_score": round(avg_score, 1),
            "distribution": {
                "excellent": excellent,
                "good": good,
                "moderate": moderate,
                "poor": poor,
            },
            "common_issues": [{"issue": k, "count": v} for k, v in common_issues],
            "pages": scored_pages,
        }

    def update_and_preview(self, page_id: int, title: str | None = None, meta_description: str | None = None) -> dict:
        """Update page meta and return fresh preview."""
        updated = self.repo.update_page_meta(page_id, title, meta_description)
        if not updated:
            raise NotFoundError("page.not_found", f"Page {page_id} not found")

        return self.generate_preview(SERPPreviewRequest(
            title=updated.get("title") or "Untitled Page",
            description=updated.get("meta_description") or "No meta description set",
            url=updated["url"],
        ))

    # ------------------------------------------------------------------
    # Truncation & Status Logic
    # ------------------------------------------------------------------

    def _truncate_title(self, title: str) -> str:
        """Truncate title like Google does (with ellipsis)."""
        if len(title) <= self.TITLE_MAX_CHARS:
            return title
        return title[:self.TITLE_MAX_CHARS - 1].rstrip() + "…"

    def _truncate_description(self, description: str) -> str:
        """Truncate description like Google does (with ellipsis)."""
        if len(description) <= self.DESCRIPTION_MAX_CHARS:
            return description
        return description[:self.DESCRIPTION_MAX_CHARS - 1].rstrip() + "…"

    def _get_title_status(self, title: str) -> str:
        """Check title length status."""
        length = len(title)
        if length > self.TITLE_MAX_CHARS:
            return "too_long"
        elif length >= self.TITLE_WARN_CHARS:
            return "warning"
        return "good"

    def _get_description_status(self, description: str) -> str:
        """Check description length status."""
        length = len(description)
        if length > self.DESCRIPTION_MAX_CHARS:
            return "too_long"
        elif length < self.DESCRIPTION_MIN_CHARS:
            return "too_short"
        elif length >= self.DESCRIPTION_WARN_CHARS:
            return "warning"
        return "good"

    def _format_display_url(self, url: str) -> str:
        """Format URL for SERP display (like Google)."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            path = parsed.path.rstrip("/")

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            # Truncate long paths
            if len(path) > 50:
                path = path[:47] + "..."

            return f"{domain}{path}"
        except Exception:
            # Fallback: just return the URL truncated
            display = url.replace("https://", "").replace("http://", "")
            if len(display) > 60:
                display = display[:57] + "..."
            return display

    # ------------------------------------------------------------------
    # Scoring & Tips
    # ------------------------------------------------------------------

    def _calculate_score(self, title: str, description: str, url: str) -> dict:
        """Calculate SERP snippet score (0-100) with breakdown and tips."""
        breakdown = {}
        tips = []

        # --- Title Score (40 points max) ---
        title_score = 0
        title_len = len(title)

        # Length scoring
        if 30 <= title_len <= 60:
            title_score += 15  # Perfect length
            tips.append({"type": "success", "text": f"Title length is optimal ({title_len} chars)"})
        elif 20 <= title_len < 30:
            title_score += 10
            tips.append({"type": "info", "text": "Title could be slightly longer (aim for 30-60 chars)"})
        elif title_len > 60:
            title_score += 5
            tips.append({"type": "warning", "text": f"Title too long ({title_len} chars) — will be truncated in search results"})
        elif title_len < 20:
            title_score += 3
            tips.append({"type": "warning", "text": "Title too short — add more descriptive keywords"})
        else:
            title_score += 8

        # Keyword in title (heuristic: check for common word patterns)
        if self._has_keyword_signals(title):
            title_score += 10
            tips.append({"type": "success", "text": "Title contains descriptive keywords"})
        else:
            tips.append({"type": "info", "text": "Include your primary keyword in the title"})

        # Compelling title signals
        if self._has_compelling_signals(title):
            title_score += 10
            tips.append({"type": "success", "text": "Title uses compelling language"})
        else:
            tips.append({"type": "info", "text": "Consider adding power words (Best, Guide, How to, etc.)"})

        # Capitalization
        if self._has_proper_capitalization(title):
            title_score += 5

        breakdown["title"] = {"score": min(title_score, 40), "max": 40}

        # --- Description Score (40 points max) ---
        desc_score = 0
        desc_len = len(description)

        # Length scoring
        if 120 <= desc_len <= 155:
            desc_score += 20  # Perfect length
            tips.append({"type": "success", "text": f"Description length is optimal ({desc_len} chars)"})
        elif 70 <= desc_len < 120:
            desc_score += 12
            tips.append({"type": "info", "text": "Description could be longer (aim for 120-155 chars)"})
        elif desc_len > 155:
            desc_score += 8
            tips.append({"type": "warning", "text": f"Description too long ({desc_len} chars) — will be truncated"})
        elif desc_len >= 50:
            desc_score += 6
            tips.append({"type": "warning", "text": "Description too short — add more detail"})
        else:
            desc_score += 2
            tips.append({"type": "error", "text": "Description is too short or missing"})

        # CTA signals
        if self._has_cta_signals(description):
            desc_score += 10
            tips.append({"type": "success", "text": "Description includes a call-to-action"})
        else:
            tips.append({"type": "info", "text": "Add a call-to-action (Learn more, Discover, Find out, etc.)"})

        # Keyword in description
        if self._has_keyword_signals(description):
            desc_score += 10
            tips.append({"type": "success", "text": "Description contains relevant keywords"})
        else:
            tips.append({"type": "info", "text": "Include relevant keywords in the description"})

        breakdown["description"] = {"score": min(desc_score, 40), "max": 40}

        # --- URL Score (20 points max) ---
        url_score = 0

        # Clean URL
        if self._has_clean_url(url):
            url_score += 10
            tips.append({"type": "success", "text": "URL is clean and readable"})
        else:
            url_score += 5
            tips.append({"type": "info", "text": "Use short, descriptive URL slugs"})

        # HTTPS
        if url.startswith("https://"):
            url_score += 5
            tips.append({"type": "success", "text": "Using HTTPS (secure)"})
        else:
            tips.append({"type": "warning", "text": "Use HTTPS for better trust and ranking"})

        # URL length
        if len(url) <= 75:
            url_score += 5
        elif len(url) <= 100:
            url_score += 3
        else:
            tips.append({"type": "info", "text": "Consider shortening the URL"})

        breakdown["url"] = {"score": min(url_score, 20), "max": 20}

        # Total score
        total_score = breakdown["title"]["score"] + breakdown["description"]["score"] + breakdown["url"]["score"]

        # Add overall tips
        if total_score >= 85:
            tips.insert(0, {"type": "success", "text": "Excellent! Your snippet is well-optimized for search results."})
        elif total_score >= 70:
            tips.insert(0, {"type": "info", "text": "Good optimization. A few tweaks could improve click-through rate."})
        elif total_score >= 50:
            tips.insert(0, {"type": "warning", "text": "Moderate optimization. Review the tips below to improve."})
        else:
            tips.insert(0, {"type": "error", "text": "Needs improvement. Follow the tips to optimize your snippet."})

        return {
            "score": total_score,
            "breakdown": breakdown,
            "tips": tips,
        }

    def _has_keyword_signals(self, text: str) -> bool:
        """Check if text contains keyword-like patterns."""
        # Simple heuristic: multiple words, not just filler
        words = text.split()
        if len(words) < 3:
            return False
        # Check for common SEO word patterns
        seo_patterns = r'\b(best|top|guide|how|what|why|tips|review|best|guide|tutorial|example|list|ideas| strategies)\b'
        return bool(re.search(seo_patterns, text, re.IGNORECASE)) or len(words) >= 5

    def _has_compelling_signals(self, title: str) -> bool:
        """Check if title uses compelling language."""
        compelling_words = r'\b(best|top|ultimate|complete|essential|proven|exclusive|free|new|secret|easy|quick|simple|powerful|amazing)\b'
        return bool(re.search(compelling_words, title, re.IGNORECASE))

    def _has_cta_signals(self, description: str) -> bool:
        """Check if description includes a call-to-action."""
        cta_words = r'\b(learn|discover|find|get|start|try|explore|read|see|check|download|sign up|join|buy|shop|compare)\b'
        return bool(re.search(cta_words, description, re.IGNORECASE))

    def _has_proper_capitalization(self, title: str) -> bool:
        """Check if title uses proper title case or sentence case."""
        if not title:
            return False
        # Title case: first letter of each major word is capitalized
        words = title.split()
        if len(words) < 2:
            return True
        # Check if most words start with capital
        caps = sum(1 for w in words if w and w[0].isupper())
        return caps >= len(words) * 0.5

    def _has_clean_url(self, url: str) -> bool:
        """Check if URL is clean and readable."""
        try:
            parsed = urlparse(url)
            path = parsed.path
            # Clean URLs: short, no query params, readable slugs
            if len(path) > 50:
                return False
            if '?' in path or '&' in path:
                return False
            # Check for readable slugs (words separated by hyphens)
            segments = [s for s in path.split('/') if s]
            return len(segments) <= 4
        except Exception:
            return False

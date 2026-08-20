"""Research orchestration: add source -> extract -> analyze (topics/claims/questions).

Rule 6: every extracted claim carries its evidence sentence. Rule 7: raw payload
is stored untouched on the source row. Extraction runs in a background thread.
"""
import re
import threading
from collections import Counter

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.database.connection import _SessionFactory
from app.integrations.podcast.extractor import extract as extract_podcast
from app.integrations.youtube.extractor import extract as extract_youtube
from app.modules.research.repository import ResearchRepository

FILE_EXTENSIONS = {"txt", "md", "markdown", "html", "htm", "csv"}

STOPWORDS = frozenset(
    "a an and are as at be but by for from has have if in into is it its of on "
    "or that the this to was we were will with you your they them he she his her "
    "so not no do does did our us i me my just about than then there here when "
    "what which who how all can more some very also been being their these those".split()
)


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResearchRepository(db)

    def add_source(
        self, source_type: str, url: str, website_id: int | None = None, title: str | None = None
    ) -> dict:
        source_id = self.repo.create_source(source_type, url=url, title=title, website_id=website_id)
        thread = threading.Thread(target=_run_extraction_job, args=(source_id,), daemon=True)
        thread.start()
        return self.repo.get_source(source_id)

    def add_file_source(self, filename: str, content: str, website_id: int | None = None) -> dict:
        """Local file dropped/opened by the user (Rule 7: raw content archived untouched)."""
        suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if suffix not in FILE_EXTENSIONS:
            raise AppError(
                "research.unsupported_file",
                f"Unsupported file type '.{suffix}' — allowed: {', '.join(sorted(FILE_EXTENSIONS))}",
            )
        if not content.strip():
            raise AppError("research.empty_file", "The file has no readable text content")

        text_content = _strip_html(content) if suffix in ("html", "htm") else content

        source_id = self.repo.create_source(
            "file", url=f"local://{filename}", title=filename, website_id=website_id,
            raw_data=text_content, availability_status="full",
        )
        # Archive the raw payload untouched, then analyze locally (no network needed)
        raw_dir = settings.data_dir / "raw" / "research"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"source{source_id}-{filename}").write_text(text_content, encoding="utf-8")

        self.repo.update_extraction(source_id, extraction_status="completed", availability_status="full")
        self.repo.add_topics(source_id, extract_topics(text_content))
        self.repo.add_claims(source_id, extract_claims(text_content))
        self.repo.add_questions(source_id, extract_questions(text_content))
        return self.repo.get_source(source_id)

    def list_sources(self, page: int, page_size: int, source_type: str | None) -> tuple[list, int]:
        return self.repo.list_sources(page, page_size, source_type)

    def get_source(self, source_id: int) -> dict | None:
        source = self.repo.get_source(source_id)
        if source is None:
            return None
        source["topics"] = self.repo.list_topics(source_id)
        source["claims"] = self.repo.list_claims(source_id)
        source["questions"] = self.repo.list_questions(source_id)
        return source

    def delete_source(self, source_id: int) -> bool:
        return self.repo.delete_source(source_id)

    # -- questions (manual + auto) ----------------------------------------------
    def add_questions(self, questions: list[str], source_id: int | None = None) -> int:
        self.repo.add_questions(source_id, questions)
        return len(questions)

    def list_questions(self, source_id: int | None) -> list[dict]:
        return self.repo.list_questions(source_id)

    def set_question_answered(self, question_id: int, answered: bool) -> None:
        self.repo.set_question_answered(question_id, answered)

    # -- content gap: questions nobody has answered ------------------------------
    def content_gap(self, source_id: int | None = None) -> list[dict]:
        return [q for q in self.repo.list_questions(source_id) if not q["answered"]]


def _run_extraction_job(source_id: int) -> None:
    """Background job with its own DB session."""
    db = _SessionFactory()
    try:
        repo = ResearchRepository(db)
        source = repo.get_source(source_id)
        if source is None:
            return
        repo.update_extraction(source_id, extraction_status="processing")

        if source["source_type"] == "youtube":
            result = extract_youtube(source["url"])
        elif source["source_type"] == "podcast":
            result = extract_podcast(source["url"])
        else:
            result = {"availability": "pending", "error": f"Unsupported source type: {source['source_type']}"}

        if result.get("error") and result.get("availability") == "pending":
            repo.update_extraction(
                source_id, extraction_status="failed",
                error_message=result["error"], availability_status="pending",
            )
            return

        # Metadata-only sources keep honest status — no fake analysis (plan §9)
        availability = result["availability"]
        if availability == "metadata_only":
            repo.update_extraction(
                source_id, extraction_status="completed", availability_status=availability,
                title=result.get("title") or result.get("show_title"), raw_data=result.get("raw"),
            )
            return

        content = result.get("transcript") or ""
        repo.update_extraction(
            source_id, extraction_status="completed", availability_status=availability,
            title=result.get("title") or result.get("show_title"), raw_data=result.get("raw"),
        )
        repo.add_topics(source_id, extract_topics(content))
        repo.add_claims(source_id, extract_claims(content))
        repo.add_questions(source_id, extract_questions(content))
    except Exception as exc:  # noqa: BLE001 — job must not kill the worker
        ResearchRepository(db).update_extraction(
            source_id, extraction_status="failed", error_message=str(exc)[:500]
        )
    finally:
        db.close()


# -- deterministic text analysis (no AI, no fabrication) -------------------------

def _strip_html(html: str) -> str:
    """Best-effort tag stripping for dropped .html files (no parser dependency)."""
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()

def extract_topics(text: str, limit: int = 10) -> list[tuple[str, float]]:
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]{3,}", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    if not counts:
        return []
    top = counts.most_common(limit)
    max_count = top[0][1]
    return [(word, round(count / max_count, 3)) for word, count in top]


def extract_claims(text: str, limit: int = 15) -> list[dict]:
    """Claim = sentence containing numbers/statistics — evidence is the sentence itself."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    claims = []
    for sentence in sentences:
        if len(sentence) < 40 or len(sentence) > 400:
            continue
        if re.search(r"\d+(?:\.\d+)?\s*(?:%|percent|million|billion|crore|lakhs?|times|x\b)", sentence):
            claims.append({
                "claim_text": sentence.strip(),
                "evidence": sentence.strip(),
                "confidence": "medium",
            })
        if len(claims) >= limit:
            break
    return claims


def extract_questions(text: str, limit: int = 10) -> list[str]:
    """Questions explicitly asked in the content — real audience questions."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    questions = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence.endswith("?") and 20 <= len(sentence) <= 200:
            questions.append(sentence)
        if len(questions) >= limit:
            break
    return questions

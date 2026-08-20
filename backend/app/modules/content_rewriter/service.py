"""Content Rewriter service — uses AI providers to generate optimized rewrites."""
import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.content_rewriter.repository import RewriteRepository

logger = logging.getLogger(__name__)

# Prompts for different content types
PROMPTS = {
    "title": (
        "You are an SEO expert. Rewrite the following page title to be more compelling and "
        "SEO-friendly while keeping it under 60 characters. Include the target keyword if provided.\n\n"
        "Original: {original}\n"
        "{context_line}\n"
        "Return exactly {num} variations, one per line. Do not number them or add any explanation."
    ),
    "description": (
        "You are an SEO expert. Rewrite the following meta description to be more compelling "
        "and click-worthy while keeping it between 120-155 characters. Include a call to action.\n\n"
        "Original: {original}\n"
        "{context_line}\n"
        "Return exactly {num} variations, one per line. Do not number them or add any explanation."
    ),
    "heading": (
        "You are an SEO expert. Rewrite the following heading (H1/H2/H3) to be more engaging "
        "and keyword-optimized while keeping it clear and concise.\n\n"
        "Original: {original}\n"
        "{context_line}\n"
        "Return exactly {num} variations, one per line. Do not number them or add any explanation."
    ),
    "custom": (
        "You are a content optimization expert. Improve the following text for clarity, "
        "engagement, and SEO. Keep the same meaning but make it more compelling.\n\n"
        "Original: {original}\n"
        "{context_line}\n"
        "Return exactly {num} variations, one per line. Do not number them or add any explanation."
    ),
}


class ContentRewriterService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RewriteRepository(db)
        self.repo.ensure_table()

    def rewrite(self, data: dict) -> dict:
        """Generate AI-powered rewrites for content."""
        content_type = data.get("content_type", "custom")
        original = data["original_text"]
        context = data.get("context", "")
        num = data.get("num_variations", 3)
        provider_override = data.get("provider")

        # Get the AI provider
        provider_name = provider_override or self._get_default_provider()
        if not provider_name:
            raise AppError("rewriter.no_provider", "No AI provider configured. Set one in Settings.")

        provider_info = self._get_provider(provider_name)
        if not provider_info:
            raise AppError("rewriter.provider_not_found", f"AI provider '{provider_name}' not found or not enabled")

        # Build the prompt
        context_line = f"Target keyword/topic: {context}" if context else ""
        prompt = PROMPTS.get(content_type, PROMPTS["custom"]).format(
            original=original, context_line=context_line, num=num,
        )

        # Call AI
        from app.integrations.ai.providers import complete
        import asyncio

        messages = [{"role": "user", "content": prompt}]
        try:
            result = asyncio.get_event_loop().run_until_complete(
                complete(provider_name, provider_info["api_key"], provider_info.get("model"), messages)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                complete(provider_name, provider_info["api_key"], provider_info.get("model"), messages)
            )
            loop.close()

        # Parse rewrites from response
        raw = result.get("content", "")
        rewrites = [line.strip() for line in raw.strip().split("\n") if line.strip()]
        # Limit to requested number
        rewrites = rewrites[:num]

        if not rewrites:
            raise AppError("rewriter.no_rewrites", "AI did not return any rewrites. Try again.")

        # Save to database
        saved = self.repo.save({
            "website_id": data.get("website_id"),
            "page_id": data.get("page_id"),
            "content_type": content_type,
            "original_text": original,
            "context": context,
            "provider": provider_name,
            "model": provider_info.get("model"),
            "rewrites": rewrites,
        })

        return {
            "id": saved["id"],
            "original": original,
            "rewrites": rewrites,
            "provider": provider_name,
            "model": provider_info.get("model"),
        }

    def select(self, request_id: int, selected_index: int) -> dict:
        result = self.repo.select_rewrite(request_id, selected_index)
        if not result:
            raise NotFoundError("rewriter.not_found", f"Rewrite request {request_id} not found")
        return result

    def apply(self, request_id: int) -> dict:
        result = self.repo.mark_applied(request_id)
        if not result:
            raise NotFoundError("rewriter.not_found", f"Rewrite request {request_id} not found")
        return result

    def history(self, website_id: int | None = None, limit: int = 50) -> list[dict]:
        return self.repo.list_recent(website_id, limit)

    def _get_default_provider(self) -> str | None:
        row = self.db.execute(
            text("SELECT provider FROM ai_providers WHERE is_default = 1 AND enabled = 1 LIMIT 1")
        ).mappings().one_or_none()
        return row.provider if row else None

    def _get_provider(self, name: str) -> dict | None:
        row = self.db.execute(
            text("SELECT * FROM ai_providers WHERE provider = :name AND enabled = 1"),
            {"name": name},
        ).mappings().one_or_none()
        if not row:
            return None
        d = dict(row)
        # Decrypt API key
        from app.core.crypto import decrypt_secret
        if d.get("api_key_encrypted"):
            d["api_key"] = decrypt_secret(d["api_key_encrypted"])
        else:
            d["api_key"] = None
        return d

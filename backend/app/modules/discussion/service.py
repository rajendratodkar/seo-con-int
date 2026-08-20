"""Discussion orchestration: human + AI conversation about content decisions.

Rule 5: AI replies are stored with role='ai' + provider label — never merged
with data-backed facts. The AI only discusses; it does not decide.
"""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.integrations.ai import providers as ai_providers
from app.modules.discussion.repository import DiscussionRepository
from app.modules.settings.service import SettingsService

SYSTEM_PROMPT = (
    "You are an SEO content strategist discussing content decisions with the site owner. "
    "Be concise and practical. When you make a claim, say what data would support it. "
    "Never present guesses as facts — label opinions as opinions."
)


class DiscussionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DiscussionRepository(db)

    def create(self, topic: str, website_id: int | None = None, idea_id: int | None = None) -> dict:
        discussion_id = self.repo.create(topic, website_id, idea_id)
        return self.repo.get(discussion_id)

    def get(self, discussion_id: int) -> dict:
        discussion = self.repo.get(discussion_id)
        if discussion is None:
            raise NotFoundError("discussion.not_found", f"Discussion {discussion_id} does not exist")
        discussion["messages"] = self.repo.list_messages(discussion_id)
        discussion["decisions"] = self.repo.list_decisions(discussion_id)
        return discussion

    def list(self, page: int, page_size: int) -> tuple[list, int]:
        return self.repo.list(page, page_size)

    async def send_message(self, discussion_id: int, content: str, ask_ai: bool, provider: str | None) -> dict:
        if self.repo.get(discussion_id) is None:
            raise NotFoundError("discussion.not_found", f"Discussion {discussion_id} does not exist")
        self.repo.add_message(discussion_id, "user", content, provider=None)
        result = {"user_message_saved": True, "ai_reply": None}
        if not ask_ai:
            return result
        credentials = SettingsService(self.db).resolve_credentials(provider)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in self.repo.list_messages(discussion_id)
        ]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
        reply = await ai_providers.complete(
            credentials["provider"], credentials["api_key"], credentials["model"], messages
        )
        self.repo.add_message(discussion_id, "ai", reply["content"], provider=reply["provider"])
        result["ai_reply"] = reply
        return result

    def decide(self, discussion_id: int, decision: str, rationale: str | None) -> dict:
        if self.repo.get(discussion_id) is None:
            raise NotFoundError("discussion.not_found", f"Discussion {discussion_id} does not exist")
        decision_id = self.repo.add_decision(discussion_id, decision, rationale)
        return {"id": decision_id, "discussion_id": discussion_id, "decision": decision}

    def archive(self, discussion_id: int) -> None:
        if self.repo.get(discussion_id) is None:
            raise NotFoundError("discussion.not_found", f"Discussion {discussion_id} does not exist")
        self.repo.set_status(discussion_id, "archived")

"""Publishing approved drafts outward: WordPress posts and GitHub/static-site commits.

Human approval gate (plan §18): only drafts with status 'approved' may leave the
app. Config secrets are encrypted at rest; raw upstream responses are archived
under data/raw/publish/ and referenced from publish_logs (Rule 7).
"""
import json
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.exceptions import AppError, NotFoundError, UpstreamError
from app.engines.content import markdown
from app.integrations.github.client import GitHubClient
from app.integrations.wordpress.client import WordPressClient
from app.modules.publishing.repository import PublishingRepository
from app.modules.settings.service import SettingsService

KNOWN_TARGETS = ("wordpress", "github")
CONFIG_KEYS = {"wordpress": "publish.wordpress", "github": "publish.github"}


class PublishingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PublishingRepository(db)
        self.settings = SettingsService(db)

    # -- configuration ------------------------------------------------------------
    def get_config(self, target: str) -> dict:
        self._check_target(target)
        raw = self.settings.get(CONFIG_KEYS[target])
        cfg = json.loads(raw) if raw else {}
        return self._public_config(target, cfg)

    def save_config(self, target: str, fields: dict) -> dict:
        self._check_target(target)
        raw = self.settings.get(CONFIG_KEYS[target])
        cfg = json.loads(raw) if raw else {}

        if target == "wordpress":
            for key in ("site_url", "user"):
                if fields.get(key) is not None:
                    cfg[key] = fields[key].strip()
            if fields.get("app_password"):
                cfg["app_password_encrypted"] = encrypt_secret(fields["app_password"])
        else:  # github
            for key in ("repo", "branch", "path_template"):
                if fields.get(key) is not None:
                    cfg[key] = fields[key].strip()
            if fields.get("token"):
                cfg["token_encrypted"] = encrypt_secret(fields["token"])

        self.settings.set(CONFIG_KEYS[target], cfg)
        return self._public_config(target, cfg)

    @staticmethod
    def _public_config(target: str, cfg: dict) -> dict:
        if target == "wordpress":
            return {
                "target": target,
                "site_url": cfg.get("site_url", ""),
                "user": cfg.get("user", ""),
                "has_app_password": bool(cfg.get("app_password_encrypted")),
            }
        return {
            "target": target,
            "repo": cfg.get("repo", ""),
            "branch": cfg.get("branch", "main"),
            "path_template": cfg.get("path_template", "src/content/blog/{slug}.md"),
            "has_token": bool(cfg.get("token_encrypted")),
        }

    def _load_config(self, target: str) -> dict:
        raw = self.settings.get(CONFIG_KEYS[target])
        return json.loads(raw) if raw else {}

    # -- WordPress ----------------------------------------------------------------
    async def test_wordpress(self) -> dict:
        client = self._wordpress_client()
        info = await client.test_connection()
        return {"connected": True, "user": info}

    async def publish_wordpress(self, draft_id: int, status: str = "draft") -> dict:
        draft = self._approved_draft(draft_id)
        client = self._wordpress_client()

        html = markdown.to_html(draft["content"])
        try:
            post = await client.create_post(draft["plan_title"], html, status=status)
        except UpstreamError as err:
            self.repo.log(draft_id, "wordpress", status, "failed", error=str(err.message))
            raise

        response_path = self._archive_response("wordpress", draft_id, post)
        log_id = self.repo.log(
            draft_id, "wordpress", status, "success",
            remote_id=str(post.get("id")), remote_url=post.get("link"),
            response_path=response_path,
        )
        return {
            "target": "wordpress", "action": status, "log_id": log_id,
            "remote_id": post.get("id"), "remote_url": post.get("link"),
            "note": "WordPress post created. The app never auto-publishes without your explicit choice.",
        }

    def _wordpress_client(self) -> WordPressClient:
        cfg = self._load_config("wordpress")
        password = decrypt_secret(cfg.get("app_password_encrypted") or "") if cfg.get("app_password_encrypted") else None
        if not cfg.get("site_url") or not cfg.get("user") or not password:
            raise AppError(
                "publish.config_missing",
                "WordPress is not configured. Set site URL, user, and application password first.",
            )
        return WordPressClient(cfg["site_url"], cfg["user"], password)

    # -- GitHub / Astro -------------------------------------------------------------
    async def publish_github(self, draft_id: int, path: str | None = None,
                             message: str | None = None) -> dict:
        draft = self._approved_draft(draft_id)
        cfg = self._load_config("github")
        token = decrypt_secret(cfg.get("token_encrypted") or "") if cfg.get("token_encrypted") else None
        if not cfg.get("repo") or not token:
            raise AppError(
                "publish.config_missing",
                "GitHub is not configured. Set repository and access token first.",
            )
        repo = cfg["repo"]
        branch = cfg.get("branch") or "main"
        slug = re.sub(r"[^a-z0-9]+", "-", draft["plan_title"].lower()).strip("-") or f"draft-{draft_id}"
        template = cfg.get("path_template") or "src/content/blog/{slug}.md"
        file_path = path or template.replace("{slug}", slug)

        client = GitHubClient(token)
        body = self._with_frontmatter(draft)
        commit_message = message or f"content: add draft '{draft['plan_title']}' (plan {draft['plan_id']})"
        try:
            sha = await client.get_file_sha(repo, file_path, branch)
            result = await client.commit_file(repo, file_path, body, commit_message, branch, sha)
        except UpstreamError as err:
            self.repo.log(draft_id, "github", "commit", "failed", error=str(err.message))
            raise

        commit = result.get("commit", {})
        response_path = self._archive_response("github", draft_id, result)
        log_id = self.repo.log(
            draft_id, "github", "commit", "success",
            remote_id=commit.get("sha"), remote_url=result.get("content", {}).get("html_url"),
            response_path=response_path,
        )
        return {
            "target": "github", "action": "commit", "log_id": log_id,
            "remote_id": commit.get("sha"),
            "remote_url": result.get("content", {}).get("html_url"),
            "path": file_path, "branch": branch,
            "note": "Committed to the branch. Trigger your site build/deploy as usual.",
        }

    @staticmethod
    def _with_frontmatter(draft: dict) -> str:
        """Astro content-collection friendly frontmatter + markdown body."""
        description = re.sub(r"\s+", " ", re.sub(r"[#*`>\[\]]", "", draft["content"]))[:160].strip()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return (
            "---\n"
            f"title: \"{draft['plan_title']}\"\n"
            f"description: \"{description}\"\n"
            f"pubDate: {today}\n"
            "draft: true\n"
            "---\n\n" + draft["content"]
        )

    # -- shared -------------------------------------------------------------------
    def _approved_draft(self, draft_id: int) -> dict:
        draft = self.repo.draft_with_plan(draft_id)
        if draft is None:
            raise NotFoundError("publish.draft_not_found", f"Draft {draft_id} does not exist")
        if draft["status"] != "approved":
            raise AppError(
                "publish.not_approved",
                f"Only approved drafts can be published (current status: {draft['status']}). "
                "Human approval is the gate before anything leaves the app.",
            )
        return draft

    def list_logs(self, draft_id: int | None = None, limit: int = 50) -> list[dict]:
        return self.repo.list_logs(draft_id, limit)

    @staticmethod
    def _archive_response(target: str, draft_id: int, payload: dict) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_dir = settings.data_dir / "raw" / "publish" / target
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"draft{draft_id}-{stamp}.json"
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return str(path)

    @staticmethod
    def _check_target(target: str) -> None:
        if target not in KNOWN_TARGETS:
            raise AppError("publish.unknown_target", f"Target must be one of {KNOWN_TARGETS}")

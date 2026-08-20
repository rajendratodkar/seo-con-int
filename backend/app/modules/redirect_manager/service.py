"""Redirect Manager service — orchestrate redirects, checks, and chain detection."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.redirect_manager.repository import RedirectManagerRepository
from app.modules.redirect_manager.schemas import (
    RedirectCreate, RedirectUpdate, RedirectBulkImport,
)


class RedirectManagerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RedirectManagerRepository(db)

    def create(self, data: RedirectCreate) -> dict:
        """Create a new redirect."""
        # Check for duplicate source
        existing = self.repo.get_redirect_by_source(data.website_id, data.source_url)
        if existing:
            raise ValueError(f"Redirect already exists for {data.source_url}")

        # Validate no self-redirect
        if data.source_url == data.target_url:
            raise ValueError("Source and target URLs cannot be the same")

        return self.repo.create_redirect(data)

    def get(self, redirect_id: int) -> dict:
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")
        return redirect

    def list(self, website_id: int, status: str | None = None, limit: int = 200) -> list[dict]:
        return self.repo.get_redirects_by_website(website_id, status, limit)

    def update(self, redirect_id: int, data: RedirectUpdate) -> dict:
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")

        # Validate no self-redirect
        if data.target_url and data.target_url == redirect["source_url"]:
            raise ValueError("Target URL cannot be the same as source URL")

        return self.repo.update_redirect(redirect_id, data)

    def delete(self, redirect_id: int) -> bool:
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")
        return self.repo.delete_redirect(redirect_id)

    def bulk_import(self, data: RedirectBulkImport) -> dict:
        """Bulk import redirects from CSV-like data."""
        count = self.repo.bulk_create(data.website_id, data.redirects, data.overwrite)
        return {"imported": count, "total_submitted": len(data.redirects)}

    def get_stats(self, website_id: int) -> dict:
        """Get redirect statistics."""
        return self.repo.get_stats(website_id)

    def detect_chains(self, website_id: int) -> list[dict]:
        """Detect redirect chains (A→B→C)."""
        chains = self.repo.detect_chains(website_id)
        # Update chain_depth for detected chains
        for chain in chains:
            self.repo.update_redirect(
                chain["id"],
                RedirectUpdate(),
            )
            # Set chain depth to 1 for simplicity
            self.db.execute(
                __import__("sqlalchemy").text(
                    "UPDATE redirects SET chain_depth = 1 WHERE id = :id"
                ),
                {"id": chain["id"]},
            )
        self.db.commit()
        return chains

    def record_check(self, redirect_id: int, status_code: int | None,
                     response_time_ms: int | None, final_url: str | None,
                     error_message: str | None = None) -> dict:
        """Record a redirect check result."""
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")
        return self.repo.add_check(redirect_id, status_code, response_time_ms, final_url, error_message)

    def get_check_history(self, redirect_id: int) -> list[dict]:
        """Get check history for a redirect."""
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")
        return self.repo.get_check_history(redirect_id)

    def resolve_chain(self, redirect_id: int) -> dict:
        """Resolve a redirect chain by pointing to the final destination."""
        redirect = self.repo.get_redirect(redirect_id)
        if not redirect:
            raise NotFoundError("redirect.not_found", f"Redirect {redirect_id} not found")

        # Follow the chain to find the final URL
        visited = {redirect["source_url"]}
        current_target = redirect["target_url"]

        while True:
            next_redirect = self.repo.get_redirect_by_source(redirect["website_id"], current_target)
            if not next_redirect or next_redirect["source_url"] in visited:
                break
            visited.add(next_redirect["source_url"])
            current_target = next_redirect["target_url"]

        # Update to point directly to final destination
        return self.repo.update_redirect(
            redirect_id,
            RedirectUpdate(target_url=current_target, chain_depth=0)
        )

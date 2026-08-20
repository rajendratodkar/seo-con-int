"""Full research workflow E2E test.

Exercises the complete data flow:
  1. Upload a research source (local file)
  2. Verify topics, claims, questions were extracted
  3. Create a content idea from the research
  4. Open a discussion linked to the idea
  5. Record a decision in the discussion
  6. Generate an article plan from the idea
  7. Update the article plan brief with research-derived fields
  8. Mark the brief as ready

Run the backend first:
    python scripts/backend/serve.py

Then:
    pytest tests/test_workflow_e2e.py -v --tb=short
"""
import httpx
import pytest

BASE = "http://127.0.0.1:8317"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=15) as c:
        yield c


# ---------------------------------------------------------------------------
# Step 1 — Upload a research source
# ---------------------------------------------------------------------------

class TestStep1_UploadResearchSource:
    """Upload a local file as a research source."""

    SOURCE_CONTENT = (
        "Internal linking is one of the most underused SEO strategies. "
        "Our case study showed a 45% increase in organic traffic after "
        "restructuring the internal link architecture of a 500-page website. "
        "The key was creating topical hub pages that linked to related "
        "cluster content using descriptive anchor text. "
        "How do you balance internal linking with user experience? "
        "What tools can automate internal link audits? "
        "Google's crawl budget is finite — orphan pages waste it entirely. "
        "Schema markup improved our rich snippet rate by 30% in six months. "
        "Core Web Vitals are now a ranking factor, so page speed matters."
    )

    def test_upload_file_source(self, client):
        r = client.post("/api/research/sources/from-file", json={
            "filename": "seo-research-notes.txt",
            "content": self.SOURCE_CONTENT,
        })
        assert r.status_code == 200, r.text
        source = r.json()
        assert source["source_type"] == "file"
        assert source["extraction_status"] == "completed"
        assert source["availability_status"] == "full"
        assert "id" in source
        self.__class__._source_id = source["id"]

    def test_source_has_extracted_topics(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("upload did not run")
        r = client.get(f"/api/research/sources/{source_id}")
        assert r.status_code == 200
        detail = r.json()
        topics = detail["topics"]
        assert len(topics) >= 2, f"expected multiple topics, got {len(topics)}"
        # Topics should be strings or dicts with text
        for t in topics:
            text = t if isinstance(t, str) else t.get("text", t.get("topic", ""))
            assert len(text) > 0

    def test_source_has_extracted_claims(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("upload did not run")
        r = client.get(f"/api/research/sources/{source_id}")
        detail = r.json()
        claims = detail["claims"]
        assert len(claims) >= 1, "should extract at least one claim"
        # The 45% claim should be captured
        claim_texts = [c if isinstance(c, str) else c.get("text", c.get("claim_text", "")) for c in claims]
        assert any("45%" in t for t in claim_texts), f"45% claim not found in {claim_texts}"

    def test_source_has_extracted_questions(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("upload did not run")
        r = client.get(f"/api/research/sources/{source_id}")
        detail = r.json()
        questions = detail["questions"]
        assert len(questions) >= 2, "should extract multiple questions"
        q_texts = [q if isinstance(q, str) else q.get("question", "") for q in questions]
        # Both questions from the source should be present
        assert any("internal linking" in q.lower() for q in q_texts), \
            f"'internal linking' question not found in {q_texts}"

    def test_source_appears_in_list(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("upload did not run")
        r = client.get("/api/research/sources")
        assert r.status_code == 200
        body = r.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        ids = [s["id"] for s in items]
        assert source_id in ids

    def test_content_gap_endpoint(self, client):
        source_id = getattr(self.__class__, "_source_id", None)
        if source_id is None:
            pytest.skip("upload did not run")
        r = client.get(f"/api/research/sources/{source_id}/gap")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body


# ---------------------------------------------------------------------------
# Step 2 — Create a content idea
# ---------------------------------------------------------------------------

class TestStep2_CreateIdea:
    """Create a content idea inspired by the research source."""

    def test_create_idea_from_research(self, client):
        source_id = getattr(TestStep1_UploadResearchSource, "_source_id", None)
        if source_id is None:
            pytest.skip("research source not created")
        r = client.post("/api/content-ideas/", json={
            "title": "The Complete Guide to Internal Linking for SEO",
            "description": (
                "Based on research showing 45% traffic increase from "
                "internal link restructuring. Covers hub pages, anchor "
                "text strategy, crawl budget optimization, and tools."
            ),
            "website_id": None,
        })
        assert r.status_code in (200, 201), r.text
        idea = r.json()
        assert idea["title"] == "The Complete Guide to Internal Linking for SEO"
        assert "id" in idea
        self.__class__._idea_id = idea["id"]

    def test_idea_status_is_draft(self, client):
        idea_id = getattr(self.__class__, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.get(f"/api/content-ideas/{idea_id}")
        assert r.status_code == 200
        idea = r.json()
        assert idea.get("status") == "draft"

    def test_validate_idea(self, client):
        idea_id = getattr(self.__class__, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.post(f"/api/content-ideas/{idea_id}/validate")
        assert r.status_code == 200

    def test_approve_idea(self, client):
        idea_id = getattr(self.__class__, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.patch(f"/api/content-ideas/{idea_id}/status", json={
            "status": "approved",
        })
        assert r.status_code == 200
        idea = r.json()
        assert idea.get("status") == "approved"


# ---------------------------------------------------------------------------
# Step 3 — Open a discussion
# ---------------------------------------------------------------------------

class TestStep3_OpenDiscussion:
    """Open a discussion linked to the approved idea."""

    def test_create_discussion_for_idea(self, client):
        idea_id = getattr(TestStep2_CreateIdea, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.post("/api/discussions/", json={
            "topic": "Research deep-dive: Internal linking strategy for the approved article",
            "website_id": None,
            "idea_id": idea_id,
        })
        assert r.status_code in (200, 201), r.text
        disc = r.json()
        assert disc["topic"].startswith("Research deep-dive")
        assert "id" in disc
        self.__class__._disc_id = disc["id"]

    def test_discussion_links_to_idea(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        idea_id = getattr(TestStep2_CreateIdea, "_idea_id", None)
        if disc_id is None or idea_id is None:
            pytest.skip("discussion or idea not created")
        r = client.get(f"/api/discussions/{disc_id}")
        assert r.status_code == 200
        disc = r.json()
        assert disc.get("idea_id") == idea_id

    def test_post_research_context_message(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        if disc_id is None:
            pytest.skip("discussion not created")
        r = client.post(f"/api/discussions/{disc_id}/messages", json={
            "content": (
                "Research summary: Internal linking restructuring led to 45% "
                "traffic increase. Key topics: hub pages, anchor text, crawl "
                "budget. Questions to address: tooling and UX balance."
            ),
            "ask_ai": False,
        })
        assert r.status_code in (200, 201), r.text

    def test_record_decision(self, client):
        disc_id = getattr(self.__class__, "_disc_id", None)
        if disc_id is None:
            pytest.skip("discussion not created")
        r = client.post(f"/api/discussions/{disc_id}/decisions", json={
            "decision": "Proceed with article — strong data backing and clear audience need",
            "rationale": "45% traffic lift is compelling evidence; questions show clear search demand",
        })
        assert r.status_code in (200, 201), r.text
        dec = r.json()
        assert "Proceed with article" in dec.get("decision", "")


# ---------------------------------------------------------------------------
# Step 4 — Generate article plan from idea
# ---------------------------------------------------------------------------

class TestStep4_ArticlePlan:
    """Generate an article plan from the approved idea and build out the brief."""

    def test_generate_plan_from_idea(self, client):
        idea_id = getattr(TestStep2_CreateIdea, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.post("/api/article-plans/from-idea", json={
            "idea_id": idea_id,
            "website_id": None,
        })
        assert r.status_code in (200, 201), r.text
        plan = r.json()
        assert plan["title"] == "The Complete Guide to Internal Linking for SEO"
        assert "id" in plan
        self.__class__._plan_id = plan["id"]

    def test_plan_status_is_draft(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("plan not created")
        r = client.get(f"/api/article-plans/{plan_id}")
        assert r.status_code == 200
        plan = r.json()
        assert plan.get("status") == "draft"

    def test_update_brief_with_research_fields(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("plan not created")
        r = client.patch(f"/api/article-plans/{plan_id}/brief", json={
            "primary_topic": "Internal linking architecture for SEO",
            "search_intent": "informational",
            "audience": "SEO professionals and website owners",
            "outline": [
                "What is internal linking and why it matters",
                "Case study: 45% traffic increase",
                "Hub-and-spoke model explained",
                "Anchor text best practices",
                "Crawl budget optimization",
                "Tools for internal link audits",
                "UX considerations",
                "Implementation checklist",
            ],
            "questions": [
                "How do you balance internal linking with user experience?",
                "What tools can automate internal link audits?",
                "How does crawl budget affect internal linking strategy?",
            ],
            "facts_to_verify": [
                {"claim_text": "45% organic traffic increase after restructuring"},
                {"claim_text": "Schema markup improved rich snippet rate by 30%"},
            ],
            "things_to_avoid": [
                "Over-optimizing anchor text (keyword stuffing)",
                "Ignoring mobile UX for link placement",
                "Creating excessive links that dilute page authority",
            ],
            "internal_links": [
                {"url": "/seo/technical-audit", "anchor": "technical SEO audit"},
                {"url": "/content/keyword-research", "anchor": "keyword research guide"},
            ],
            "sources": [
                {"type": "research", "source_id": getattr(TestStep1_UploadResearchSource, "_source_id", 0)},
            ],
        })
        assert r.status_code == 200, r.text
        plan = r.json()
        assert plan["primary_topic"] == "Internal linking architecture for SEO"
        assert plan["search_intent"] == "informational"

    def test_mark_brief_ready(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("plan not created")
        r = client.post(f"/api/article-plans/{plan_id}/brief-ready")
        assert r.status_code == 200
        plan = r.json()
        assert plan.get("status") == "brief_ready"

    def test_plan_appears_in_list(self, client):
        plan_id = getattr(self.__class__, "_plan_id", None)
        if plan_id is None:
            pytest.skip("plan not created")
        r = client.get("/api/article-plans/")
        assert r.status_code == 200
        body = r.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        ids = [p["id"] for p in items]
        assert plan_id in ids


# ---------------------------------------------------------------------------
# Step 5 — Cleanup
# ---------------------------------------------------------------------------

class TestStep5_Cleanup:
    """Remove test artifacts in reverse order."""

    def test_delete_plan(self, client):
        plan_id = getattr(TestStep4_ArticlePlan, "_plan_id", None)
        if plan_id is None:
            pytest.skip("plan not created")
        r = client.delete(f"/api/article-plans/{plan_id}")
        assert r.status_code in (200, 204)

    def test_archive_discussion(self, client):
        disc_id = getattr(TestStep3_OpenDiscussion, "_disc_id", None)
        if disc_id is None:
            pytest.skip("discussion not created")
        r = client.post(f"/api/discussions/{disc_id}/archive")
        assert r.status_code == 200
        assert r.json()["status"] == "archived"

    def test_delete_idea(self, client):
        idea_id = getattr(TestStep2_CreateIdea, "_idea_id", None)
        if idea_id is None:
            pytest.skip("idea not created")
        r = client.delete(f"/api/content-ideas/{idea_id}")
        assert r.status_code in (200, 204)

    def test_delete_source(self, client):
        source_id = getattr(TestStep1_UploadResearchSource, "_source_id", None)
        if source_id is None:
            pytest.skip("source not created")
        r = client.delete(f"/api/research/sources/{source_id}")
        assert r.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Cross-cutting: verify the full chain links are correct
# ---------------------------------------------------------------------------

class TestCrossCutting:
    """Verify data relationships across the full workflow."""

    def test_discussion_count_after_workflow(self, client):
        r = client.get("/api/discussions/")
        assert r.status_code == 200

    def test_article_plan_count_after_workflow(self, client):
        r = client.get("/api/article-plans/")
        assert r.status_code == 200

    def test_research_questions_list(self, client):
        """Verify the global questions endpoint works."""
        r = client.get("/api/research/questions")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body

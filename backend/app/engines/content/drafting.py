"""AI drafting engine: brief -> context -> labeled draft.

The context fed to the AI contains ONLY verified data (plan evidence, Search
Console numbers, human-approved outline). The returned text is an
`ai_suggestion` until a human edits/approves it (Rule 5).
"""
import json

from app.integrations.ai import providers as ai_providers

SYSTEM_PROMPT = (
    "You are a professional SEO content writer. Write the article draft in Markdown "
    "following the provided brief exactly. Rules:\n"
    "- Use ONLY the facts given in the brief. Do not invent statistics, names, or dates.\n"
    "- Where the brief lists facts_to_verify, add a placeholder like [VERIFY: ...].\n"
    "- Structure the article with H2/H3 headings matching the outline.\n"
    "- Keep a neutral, helpful tone. No hype."
)


def build_user_prompt(plan: dict) -> str:
    def _load(field: str, default):
        try:
            return json.loads(plan.get(field) or "null") or default
        except (json.JSONDecodeError, TypeError):
            return default

    outline = _load("outline", [])
    questions = _load("questions", [])
    facts = _load("facts_to_verify", [])
    sc_evidence = _load("sc_evidence", [])
    avoid = _load("things_to_avoid", [])

    parts = [
        f"# Brief: {plan['title']}",
        f"Primary topic: {plan.get('primary_topic') or plan['title']}",
        f"Search intent: {plan.get('search_intent') or 'informational'}",
    ]
    if plan.get("audience"):
        parts.append(f"Audience: {plan['audience']}")
    if outline:
        parts.append("\n## Outline\n" + "\n".join(
            f"- {item}" if isinstance(item, str) else f"- {json.dumps(item)}" for item in outline
        ))
    if questions:
        parts.append("\n## Questions the article must answer\n" + "\n".join(f"- {q}" for q in questions))
    if facts:
        parts.append("\n## Facts to verify (use [VERIFY: ...] placeholders)\n" + "\n".join(
            f"- {f['claim_text'] if isinstance(f, dict) else f}" for f in facts
        ))
    if sc_evidence:
        parts.append("\n## Search Console evidence (real data — safe to reference)\n" + "\n".join(
            f"- query '{e['query']}': {e['impressions']} impressions, position {e.get('avg_position')}"
            for e in sc_evidence if isinstance(e, dict)
        ))
    if avoid:
        parts.append("\n## Avoid\n" + "\n".join(f"- {a}" for a in avoid))
    parts.append("\nWrite the full article draft now.")
    return "\n".join(parts)


async def draft(plan: dict, provider_name: str, api_key: str, model: str | None) -> dict:
    """Returns {content, provider, model} — caller stores it labeled as ai_suggestion."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(plan)},
    ]
    return await ai_providers.complete(provider_name, api_key, model, messages)

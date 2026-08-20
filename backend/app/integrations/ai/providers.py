"""AI provider clients: OpenAI, Gemini, Anthropic (plain REST via httpx).

Rule 5: AI output is NEVER presented as truth. Every AI response returned from
this layer is labeled with its provider + model so callers can mark it as an
`ai_suggestion`.
"""
import httpx

from app.core.http import http_client

from app.core.exceptions import UpstreamError

TIMEOUT = 60.0

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-3-5-haiku-latest",
}


async def complete(provider: str, api_key: str, model: str | None, messages: list[dict]) -> dict:
    """messages: [{role: system|user|assistant, content}] -> {content, provider, model}."""
    model = model or DEFAULT_MODELS.get(provider)
    if provider == "openai":
        return await _openai(api_key, model, messages)
    if provider == "gemini":
        return await _gemini(api_key, model, messages)
    if provider == "anthropic":
        return await _anthropic(api_key, model, messages)
    raise UpstreamError("ai.unknown_provider", f"Unknown AI provider: {provider}")


async def _openai(api_key: str, model: str, messages: list[dict]) -> dict:
    async with http_client(timeout=TIMEOUT) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages},
        )
    _check(response, "openai")
    data = response.json()
    return {"content": data["choices"][0]["message"]["content"], "provider": "openai", "model": model}


async def _gemini(api_key: str, model: str, messages: list[dict]) -> dict:
    system = " ".join(m["content"] for m in messages if m["role"] == "system")
    contents = [
        {"role": "user" if m["role"] != "assistant" else "model", "parts": [{"text": m["content"]}]}
        for m in messages if m["role"] != "system"
    ]
    body: dict = {"contents": contents}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    async with http_client(timeout=TIMEOUT) as client:
        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            json=body,
        )
    _check(response, "gemini")
    data = response.json()
    return {"content": data["candidates"][0]["content"]["parts"][0]["text"], "provider": "gemini", "model": model}


async def _anthropic(api_key: str, model: str, messages: list[dict]) -> dict:
    system = " ".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] in ("user", "assistant")]
    async with http_client(timeout=TIMEOUT) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 2048, "system": system, "messages": turns},
        )
    _check(response, "anthropic")
    data = response.json()
    return {"content": data["content"][0]["text"], "provider": "anthropic", "model": model}


def _check(response: httpx.Response, provider: str) -> None:
    if response.status_code >= 400:
        try:
            details = response.json()
        except ValueError:
            details = {"body": response.text[:300]}
        raise UpstreamError(f"{provider}.api_error", f"{provider} API returned {response.status_code}", details=details)

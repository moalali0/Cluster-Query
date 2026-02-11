"""Ollama LLM async client for structured chatbot."""

import json
import logging
from typing import Any, AsyncIterator

import httpx

from .config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a contract precedent analyst. Your job is to summarise retrieved clause clusters "
    "for the user. Rules:\n"
    "1. ONLY use information from the provided evidence clusters. Never fabricate.\n"
    "2. Cite cluster IDs in square brackets, e.g. [cluster_id].\n"
    "3. Do NOT provide legal advice. State observations from the data.\n"
    "4. Be concise. Use bullet points when listing multiple precedents.\n"
    "5. If no relevant evidence is provided, say so clearly."
)

_TIMEOUT = httpx.Timeout(connect=60.0, read=300.0, write=10.0, pool=10.0)


def _format_context(results: list[dict[str, Any]]) -> str:
    """Format retrieved clusters into context for the LLM."""
    if not results:
        return "No evidence clusters were retrieved."

    parts: list[str] = []
    for r in results:
        cid = str(r["id"])[:8]
        client = r.get("client_id", "unknown")
        score = float(r.get("relevance_score", 0))
        codified = json.dumps(r.get("codified_data") or {}, indent=2)
        text = (r.get("text_content") or "")[:500]
        parts.append(
            f"--- Cluster {cid} (bank={client}, relevance={score:.3f}) ---\n"
            f"Codified data:\n{codified}\n"
            f"Clause text:\n{text}\n"
        )
    return "\n".join(parts)


def build_chat_messages(
    results: list[dict[str, Any]],
    term: str | None = None,
    attribute: str | None = None,
    language: str | None = None,
) -> list[dict[str, str]]:
    """Assemble system + user messages for the LLM."""
    context = _format_context(results)

    criteria_parts: list[str] = []
    if term:
        criteria_parts.append(f"Term: {term}")
    if attribute:
        criteria_parts.append(f"Attribute: {attribute}")
    if language:
        criteria_parts.append(f"Language: {language}")
    criteria = ", ".join(criteria_parts) if criteria_parts else "General search"

    user_msg = (
        f"Search criteria: {criteria}\n\n"
        f"Retrieved evidence:\n{context}\n\n"
        "Please summarise the relevant precedents found across these clusters. "
        "Highlight key patterns, differences between banks, and cite cluster IDs."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]


async def chat_completion_stream(
    messages: list[dict[str, str]],
) -> AsyncIterator[str]:
    """Stream tokens from Ollama /api/chat endpoint."""
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": settings.llm_temperature,
            "num_predict": settings.llm_max_tokens,
        },
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{settings.ollama_host}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break


async def check_ollama_health() -> dict[str, Any]:
    """Check if Ollama is reachable and report loaded model."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            model_names = [m.get("name", "") for m in data.get("models", [])]
            model_loaded = settings.ollama_model in model_names
            return {
                "ollama_reachable": True,
                "ollama_model": settings.ollama_model,
                "model_loaded": model_loaded,
                "available_models": model_names,
            }
    except Exception as exc:
        logger.warning("Ollama health check failed: %s", exc)
        return {
            "ollama_reachable": False,
            "ollama_model": settings.ollama_model,
            "model_loaded": False,
            "error": str(exc),
        }

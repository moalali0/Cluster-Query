"""Ollama LLM async client for structured chatbot."""

import json
import logging
from typing import Any, AsyncIterator

import httpx

from .config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful contract precedent assistant. "
    "You explain what was found in a simple, conversational way — like a senior colleague briefing an analyst.\n\n"
    "Rules:\n"
    "1. ONLY use information from the provided clusters. Never make things up.\n"
    "2. Refer to clusters by their short ID in square brackets, e.g. [7a4638ab].\n"
    "3. Do NOT give legal advice. Just describe what the data shows.\n"
    "4. Use plain English. Avoid jargon unless it comes directly from the data.\n"
    "5. For each cluster, explain:\n"
    "   - What the clause language says (quote it briefly)\n"
    "   - What was codified (the structured fields and values)\n"
    "   - If there is a query history, mention what was discussed between analyst and client\n"
    "   - Which client environment (bank) it belongs to\n"
    "6. After covering individual clusters, briefly note any patterns — e.g. if multiple banks "
    "use similar language, or if there are notable differences.\n"
    "7. Keep it concise. A few sentences per cluster is enough.\n"
    "8. If no relevant evidence is provided, say so clearly."
)

_TIMEOUT = httpx.Timeout(connect=60.0, read=300.0, write=10.0, pool=10.0)


def _format_context(results: list[dict[str, Any]]) -> str:
    """Format retrieved clusters into plain-English context for the LLM."""
    if not results:
        return "No clusters were retrieved."

    parts: list[str] = []
    for r in results:
        cid = str(r["id"])[:8]
        client = r.get("client_id", "unknown")

        # Codified fields as readable key-value pairs
        codified_data = r.get("codified_data") or {}
        codified_lines: list[str] = []
        for term_key, attrs in codified_data.items():
            if isinstance(attrs, dict):
                for attr_key, val in attrs.items():
                    codified_lines.append(f"  {term_key} > {attr_key}: {val}")
            else:
                codified_lines.append(f"  {term_key}: {attrs}")
        codified_str = "\n".join(codified_lines) if codified_lines else "  (none)"

        # Clause language
        text = (r.get("text_content") or "").strip()
        clause_str = f'"{text[:600]}"' if text else "(no clause text)"

        # Query history
        history = r.get("query_history") or []
        if isinstance(history, str):
            try:
                history = json.loads(history)
            except (json.JSONDecodeError, TypeError):
                history = []
        history_lines: list[str] = []
        for entry in history:
            if isinstance(entry, dict):
                role = entry.get("role", "Unknown")
                msg = entry.get("query") or entry.get("response") or ""
                if msg:
                    history_lines.append(f"  {role}: {msg}")
        history_str = "\n".join(history_lines) if history_lines else "  (no queries)"

        parts.append(
            f"--- Cluster {cid} ---\n"
            f"Client environment: {client}\n"
            f"Clause language: {clause_str}\n"
            f"Codified fields:\n{codified_str}\n"
            f"Query history:\n{history_str}\n"
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
        f"The user searched for: {criteria}\n\n"
        f"Here are the clusters that matched:\n\n{context}\n\n"
        "Walk through each cluster and explain what it contains in plain language. "
        "For each one, mention:\n"
        "- What the clause says (quote briefly)\n"
        "- What was codified from it\n"
        "- Any queries or discussions that took place on it\n"
        "- Which client environment (bank) it sits in\n\n"
        "Then briefly note any patterns or differences across the clusters."
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

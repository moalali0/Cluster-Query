"""Ollama LLM async client for structured chatbot."""

import json
import logging
from typing import Any, AsyncIterator

import httpx

from .config import settings
from .language import get_language_instruction
from .prompts import get_prompt_for_term

logger = logging.getLogger(__name__)

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
    """Assemble system + user messages for the LLM.

    Uses the prompt registry for term-specific prompts and appends
    language instructions when non-English clauses are detected.
    """
    template = get_prompt_for_term(term)
    context = _format_context(results)

    criteria_parts: list[str] = []
    if term:
        criteria_parts.append(f"Term: {term}")
    if attribute:
        criteria_parts.append(f"Attribute: {attribute}")
    if language:
        criteria_parts.append(f"Language: {language}")
    criteria = ", ".join(criteria_parts) if criteria_parts else "General search"

    system_prompt = template.system_prompt
    lang_instruction = get_language_instruction(results)
    if lang_instruction:
        system_prompt += f"\n\nLanguage note: {lang_instruction}"

    user_msg = template.user_template.format(criteria=criteria, context=context)

    return [
        {"role": "system", "content": system_prompt},
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

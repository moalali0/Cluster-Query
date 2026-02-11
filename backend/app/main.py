import asyncio
import json
import time
from typing import Any

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .audit import log_api_event
from .config import settings
from .db import get_app_conn
from .embeddings import embed_text
from .llm import build_chat_messages, chat_completion_stream, check_ollama_health
from .retrieval import search_clusters_across_clients, search_clusters_structured_across_clients
from .schemas import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    StructuredChatRequest,
    StructuredSearchRequest,
)

app = FastAPI(title="Secure Internal Contract AI - Phase 0")
GLOBAL_SCOPE = "ALL_BANKS"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    result = {"status": "ok"}
    if settings.llm_enabled:
        ollama_status = await check_ollama_health()
        result.update(ollama_status)
    else:
        result["llm_enabled"] = False
    return result


def _filter_results(raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in raw_results if float(r["relevance_score"]) >= settings.similarity_threshold]


def _top_score(raw_results: list[dict[str, Any]]) -> float | None:
    if not raw_results:
        return None
    return float(raw_results[0]["relevance_score"])


def _safe_log_event(**kwargs: Any) -> None:
    conn = kwargs.pop("conn")
    try:
        log_api_event(conn, **kwargs)
    except Exception:
        conn.rollback()


def _build_answer(filtered: list[dict[str, Any]]) -> tuple[str, list[str]]:
    top = filtered[0]
    citations = [str(r["id"]) for r in filtered[:3]]
    citation_marks = " ".join(f"[{i + 1}]" for i in range(len(citations)))
    answer = (
        "Based on historical cluster decisions, this language has prior captures. "
        f"Top precedent codification: {top['codified_data']}. "
        "Client clarification context appears in the cited query history. "
        f"Evidence: {citation_marks}"
    )
    return answer, citations


def _sse(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@app.post("/api/search", response_model=SearchResponse)
def api_search(
    payload: SearchRequest,
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> SearchResponse:
    started = time.perf_counter()
    query_embedding = embed_text(payload.query)
    target_clients = settings.allowed_client_list

    with get_app_conn() as conn:
        raw_results = search_clusters_across_clients(conn, target_clients, query_embedding, payload.top_k)
        filtered = _filter_results(raw_results)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        _safe_log_event(
            conn=conn,
            client_id=GLOBAL_SCOPE,
            user_id=x_user_id,
            endpoint="/api/search",
            query_text=payload.query,
            result_count=len(filtered),
            evidence_found=bool(filtered),
            top_score=_top_score(raw_results),
            status_code=200,
            response_time_ms=elapsed_ms,
            error_message=None,
        )

        conn.commit()

    if not filtered:
        return SearchResponse(
            query=payload.query,
            scope=GLOBAL_SCOPE,
            threshold=settings.similarity_threshold,
            evidence_found=False,
            note="Insufficient evidence for a trustworthy precedent answer.",
            results=[],
            searched_clients=target_clients,
        )

    return SearchResponse(
        query=payload.query,
        scope=GLOBAL_SCOPE,
        threshold=settings.similarity_threshold,
        evidence_found=True,
        note=f"Evidence-backed precedents found across {len(target_clients)} bank streams.",
        results=filtered,
        searched_clients=target_clients,
    )


@app.post("/api/chat", response_model=ChatResponse)
def api_chat(
    payload: ChatRequest,
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> ChatResponse:
    started = time.perf_counter()
    query_embedding = embed_text(payload.query)
    target_clients = settings.allowed_client_list

    with get_app_conn() as conn:
        raw_results = search_clusters_across_clients(conn, target_clients, query_embedding, settings.default_top_k)
        filtered = _filter_results(raw_results)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        if not filtered:
            _safe_log_event(
                conn=conn,
                client_id=GLOBAL_SCOPE,
                user_id=x_user_id,
                endpoint="/api/chat",
                query_text=payload.query,
                result_count=0,
                evidence_found=False,
                top_score=_top_score(raw_results),
                status_code=200,
                response_time_ms=elapsed_ms,
                error_message="insufficient_evidence",
            )
            conn.commit()
            return ChatResponse(
                answer="I cannot answer from precedent because no sufficiently similar, in-scope clusters were found.",
                citations=[],
                evidence_found=False,
            )

        answer, citations = _build_answer(filtered)
        _safe_log_event(
            conn=conn,
            client_id=GLOBAL_SCOPE,
            user_id=x_user_id,
            endpoint="/api/chat",
            query_text=payload.query,
            result_count=len(filtered),
            evidence_found=True,
            top_score=_top_score(raw_results),
            status_code=200,
            response_time_ms=elapsed_ms,
            error_message=None,
        )
        conn.commit()

    return ChatResponse(answer=answer, citations=citations, evidence_found=True)


@app.post("/api/chat/stream")
async def api_chat_stream(
    payload: ChatRequest,
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> StreamingResponse:
    started = time.perf_counter()
    query_embedding = embed_text(payload.query)
    target_clients = settings.allowed_client_list

    with get_app_conn() as conn:
        raw_results = search_clusters_across_clients(conn, target_clients, query_embedding, settings.default_top_k)
        filtered = _filter_results(raw_results)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        if not filtered:
            answer = "I cannot answer from precedent because no sufficiently similar, in-scope clusters were found."
            citations: list[str] = []
            evidence_found = False
            error_message = "insufficient_evidence"
        else:
            answer, citations = _build_answer(filtered)
            evidence_found = True
            error_message = None

        _safe_log_event(
            conn=conn,
            client_id=GLOBAL_SCOPE,
            user_id=x_user_id,
            endpoint="/api/chat/stream",
            query_text=payload.query,
            result_count=len(filtered),
            evidence_found=evidence_found,
            top_score=_top_score(raw_results),
            status_code=200,
            response_time_ms=elapsed_ms,
            error_message=error_message,
        )
        conn.commit()

    async def event_generator():
        yield _sse(
            "meta",
            {
                "evidence_found": evidence_found,
                "scope": GLOBAL_SCOPE,
                "searched_clients": target_clients,
            },
        )
        for token in answer.split(" "):
            yield _sse("token", {"token": token + " "})
            await asyncio.sleep(0.02)
        yield _sse(
            "done",
            {
                "citations": citations,
                "evidence_found": evidence_found,
                "token_count": len(answer.split(" ")),
            },
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ---------- Structured endpoints ----------


def _do_structured_search(
    payload: StructuredSearchRequest | StructuredChatRequest,
    top_k: int,
) -> list[dict]:
    """Run structured retrieval across all allowed clients."""
    embedding = embed_text(payload.language) if payload.language else None
    target_clients = settings.allowed_client_list

    with get_app_conn() as conn:
        raw = search_clusters_structured_across_clients(
            conn,
            target_clients,
            top_k,
            term=payload.term,
            attribute=payload.attribute,
            embedding=embedding,
        )
        conn.commit()
    return raw


@app.post("/api/search/structured", response_model=SearchResponse)
def api_search_structured(
    payload: StructuredSearchRequest,
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> SearchResponse:
    started = time.perf_counter()
    target_clients = settings.allowed_client_list
    raw_results = _do_structured_search(payload, payload.top_k)
    filtered = _filter_results(raw_results) if payload.language else raw_results
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    query_text = " | ".join(
        f for f in [payload.term, payload.attribute, payload.language] if f
    )

    with get_app_conn() as conn:
        _safe_log_event(
            conn=conn,
            client_id=GLOBAL_SCOPE,
            user_id=x_user_id,
            endpoint="/api/search/structured",
            query_text=query_text,
            result_count=len(filtered),
            evidence_found=bool(filtered),
            top_score=_top_score(raw_results),
            status_code=200,
            response_time_ms=elapsed_ms,
            error_message=None,
        )
        conn.commit()

    if not filtered:
        return SearchResponse(
            query=query_text,
            scope=GLOBAL_SCOPE,
            threshold=settings.similarity_threshold,
            evidence_found=False,
            note="No matching precedents found for the given criteria.",
            results=[],
            searched_clients=target_clients,
        )

    return SearchResponse(
        query=query_text,
        scope=GLOBAL_SCOPE,
        threshold=settings.similarity_threshold,
        evidence_found=True,
        note=f"Structured search found {len(filtered)} precedent(s) across {len(target_clients)} bank streams.",
        results=filtered,
        searched_clients=target_clients,
    )


@app.post("/api/chat/structured/stream")
async def api_chat_structured_stream(
    payload: StructuredChatRequest,
    x_user_id: str = Header(default="demo-analyst", alias="x-user-id"),
) -> StreamingResponse:
    started = time.perf_counter()
    target_clients = settings.allowed_client_list
    raw_results = _do_structured_search(payload, settings.default_top_k)
    filtered = _filter_results(raw_results) if payload.language else raw_results
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    query_text = " | ".join(
        f for f in [payload.term, payload.attribute, payload.language] if f
    )

    evidence_found = bool(filtered)

    with get_app_conn() as conn:
        _safe_log_event(
            conn=conn,
            client_id=GLOBAL_SCOPE,
            user_id=x_user_id,
            endpoint="/api/chat/structured/stream",
            query_text=query_text,
            result_count=len(filtered),
            evidence_found=evidence_found,
            top_score=_top_score(raw_results),
            status_code=200,
            response_time_ms=elapsed_ms,
            error_message=None if evidence_found else "insufficient_evidence",
        )
        conn.commit()

    async def event_generator():
        meta_payload = {
            "evidence_found": evidence_found,
            "scope": GLOBAL_SCOPE,
            "searched_clients": target_clients,
            "llm_model": settings.ollama_model if settings.llm_enabled else None,
        }
        yield _sse("meta", meta_payload)

        if not evidence_found:
            yield _sse("token", {"token": "No matching precedents found for the given criteria."})
            yield _sse("done", {"citations": [], "evidence_found": False, "token_count": 0})
            return

        citations = [str(r["id"]) for r in filtered[:3]]

        if settings.llm_enabled:
            try:
                messages = build_chat_messages(
                    filtered,
                    term=payload.term,
                    attribute=payload.attribute,
                    language=payload.language,
                )
                token_count = 0
                async for token in chat_completion_stream(messages):
                    yield _sse("token", {"token": token})
                    token_count += 1
                yield _sse(
                    "done",
                    {"citations": citations, "evidence_found": True, "token_count": token_count},
                )
            except Exception as exc:
                yield _sse("error", {"message": f"LLM error: {exc}"})
                # Fall back to template answer
                answer, citations = _build_answer(filtered)
                for token in answer.split(" "):
                    yield _sse("token", {"token": token + " "})
                    await asyncio.sleep(0.02)
                yield _sse(
                    "done",
                    {"citations": citations, "evidence_found": True, "token_count": len(answer.split(" "))},
                )
        else:
            answer, citations = _build_answer(filtered)
            for token in answer.split(" "):
                yield _sse("token", {"token": token + " "})
                await asyncio.sleep(0.02)
            yield _sse(
                "done",
                {"citations": citations, "evidence_found": True, "token_count": len(answer.split(" "))},
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
from .retrieval import search_clusters_across_clients
from .schemas import ChatRequest, ChatResponse, SearchRequest, SearchResponse

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
def health() -> dict[str, str]:
    return {"status": "ok"}


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

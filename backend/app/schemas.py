from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)


class ClusterResult(BaseModel):
    id: UUID
    client_id: str
    text_content: str
    codified_data: dict[str, Any] | None
    query_history: list[dict[str, Any]] | None
    doc_count: int | None
    last_updated: datetime | None
    relevance_score: float


class SearchResponse(BaseModel):
    query: str
    scope: str
    threshold: float
    evidence_found: bool
    note: str
    results: list[ClusterResult]
    searched_clients: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2)


class ChatResponse(BaseModel):
    answer: str
    citations: list[str]
    evidence_found: bool

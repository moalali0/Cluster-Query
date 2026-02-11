from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class StructuredSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str | None = Field(default=None, description="Top-level codified_data key, e.g. 'Governing Law'")
    attribute: str | None = Field(default=None, description="Nested key within term, e.g. 'Jurisdiction'")
    language: str | None = Field(default=None, min_length=2, description="Free-text for embedding search")
    top_k: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.term and not self.attribute and not self.language:
            raise ValueError("At least one of term, attribute, or language is required")
        return self


class StructuredChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str | None = Field(default=None, description="Top-level codified_data key")
    attribute: str | None = Field(default=None, description="Nested key within term")
    language: str | None = Field(default=None, min_length=2, description="Free-text for embedding search")

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.term and not self.attribute and not self.language:
            raise ValueError("At least one of term, attribute, or language is required")
        return self

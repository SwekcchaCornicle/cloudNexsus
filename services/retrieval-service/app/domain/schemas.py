"""Pydantic API contracts; validate inputs and stabilize the JSON response shape."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator

Provider = Literal["AWS", "AZURE", "GCP"]


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    provider: Provider | None = None
    service_name: str | None = Field(default=None, max_length=100)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class RetrievedEntity(BaseModel):
    name: str
    canonical_name: str | None = None
    provider: str | None = None


class RetrievedRelationship(BaseModel):
    source: str
    predicate: str
    target: str
    evidence: str | None = None
    confidence: float | None = None


class RetrievalResult(BaseModel):
    chunk_id: str
    content: str
    score: float

    # Hybrid retrieval metadata
    rrf_score: float | None = None
    retrieval_sources: list[str] = Field(default_factory=list)

    provider: str | None = None
    service_name: str | None = None
    source_url: str | None = None
    document_id: str | None = None
    embedding_model: str | None = None

    entities: list[RetrievedEntity] = Field(default_factory=list)
    relationships: list[RetrievedRelationship] = Field(default_factory=list)


class RetrievalResponse(BaseModel):
    question: str
    provider_filter: str | None = None
    result_count: int
    results: list[RetrievalResult]
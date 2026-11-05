from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, field_validator

class Provider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"

class DocumentMetadata(BaseModel):
    document_id: str
    provider: Provider
    service_name: str
    source_url: HttpUrl
    title: str
    filename: str
    checksum_sha256: str
    pipeline_version: str = "0.1.0"

class InputChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    chunk_id: str
    document_id: str
    provider: Provider
    service_name: str
    title: str
    source_url: HttpUrl
    chunk_index: int = Field(ge=0)
    heading_path: list[str] = Field(default_factory=list)
    content: str = Field(min_length=1)
    approximate_token_count: int = Field(ge=0)
    content_hash: str

class IngestionArtifact(BaseModel):
    metadata: DocumentMetadata
    chunks: list[InputChunk] = Field(min_length=1)

    @field_validator("chunks")
    @classmethod
    def chunks_belong_to_document(cls, chunks, info):
        metadata = info.data.get("metadata")
        if metadata and any(c.document_id != metadata.document_id for c in chunks):
            raise ValueError("Every chunk must belong to the artifact document_id.")
        return chunks

class ExtractedEntity(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    canonical_name: str = Field(min_length=1, max_length=200)
    entity_type: str = Field(min_length=2, max_length=80)
    provider: Provider | None = None
    description: str = Field(default="", max_length=1000)

class ExtractedRelationship(BaseModel):
    source_entity: str
    target_entity: str
    predicate: str = Field(min_length=2, max_length=100)
    # Evidence must be an exact source excerpt. Its natural upper bound is the
    # source chunk length, so a fixed 1000/1500-character cap rejects valid
    # evidence from longer chunks. ExtractionService verifies that the
    # normalized evidence is present in the original chunk before saving.
    evidence: str = Field(min_length=5)
    confidence: float = Field(ge=0.0, le=1.0)

class KnowledgeExtraction(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)

class ExtractedChunk(BaseModel):
    chunk_id: str
    document_id: str
    provider: Provider
    service_name: str
    source_url: str
    heading_path: list[str]
    content: str
    embedding: list[float]
    embedding_model_id: str
    extraction: KnowledgeExtraction

class ExtractionArtifact(BaseModel):
    document_id: str
    provider: Provider
    title: str
    source_url: str
    extraction_mode: str
    chunk_count: int
    chunks: list[ExtractedChunk]

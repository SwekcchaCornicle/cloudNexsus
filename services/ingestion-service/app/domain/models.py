from enum import Enum
from pydantic import BaseModel, Field


class Provider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"


class ContentBlock(BaseModel):
    heading_path: list[str] = Field(default_factory=list)
    block_type: str
    text: str


class DocumentMetadata(BaseModel):
    document_id: str
    provider: Provider
    service_name: str
    source_url: str
    title: str
    filename: str
    checksum_sha256: str
    pipeline_version: str = "0.1.0"


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    provider: Provider
    service_name: str
    title: str
    source_url: str
    chunk_index: int
    heading_path: list[str]
    content: str
    approximate_token_count: int
    content_hash: str

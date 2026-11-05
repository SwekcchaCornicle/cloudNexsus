from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from app.domain.models import Provider, DocumentMetadata, ChunkRecord
from app.services.html_extractor import extract_html
from app.services.chunker import chunk_blocks, sha256_text


class IngestionService:
    def __init__(self, artifact_store, max_words: int = 600, overlap_words: int = 80):
        self.artifact_store = artifact_store
        self.max_words = max_words
        self.overlap_words = overlap_words

    def process(
        self,
        raw_bytes: bytes,
        filename: str,
        provider: Provider,
        service_name: str,
        source_url: str,
    ) -> dict:
        try:
            html = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("HTML must be UTF-8 encoded.") from exc

        if "<" not in html or ">" not in html:
            raise ValueError("Uploaded content does not appear to be HTML.")

        document_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        checksum = hashlib.sha256(raw_bytes).hexdigest()

        title, blocks = extract_html(html)
        if not blocks:
            raise ValueError("No readable content was extracted from the HTML.")

        grouped_chunks = chunk_blocks(
            blocks,
            max_words=self.max_words,
            overlap_words=self.overlap_words,
        )

        metadata = DocumentMetadata(
            document_id=document_id,
            provider=provider,
            service_name=service_name,
            source_url=source_url,
            title=title,
            filename=filename,
            checksum_sha256=checksum,
        )

        chunks = []
        for index, (heading_path, content, word_count) in enumerate(grouped_chunks):
            chunk_id = f"{document_id}:{index:05d}"
            chunks.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    provider=provider,
                    service_name=service_name,
                    title=title,
                    source_url=source_url,
                    chunk_index=index,
                    heading_path=heading_path,
                    content=content,
                    approximate_token_count=word_count,
                    content_hash=sha256_text(content),
                )
            )

        artifact = {
            "metadata": metadata.model_dump(mode="json"),
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "chunk_count": len(chunks),
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }
        paths = self.artifact_store.save(
            document_id=document_id,
            job_id=job_id,
            filename=filename,
            raw_bytes=raw_bytes,
            artifact=artifact,
        )

        result = {
            "job_id": job_id,
            "document_id": document_id,
            "provider": provider.value,
            "service_name": service_name,
            "status": "COMPLETED",
            "title": title,
            "chunk_count": len(chunks),
            "checksum_sha256": checksum,
            "raw_artifact": paths["raw"],
            "processed_artifact": paths["processed"],
        }
        self.artifact_store.save_job(job_id, result)
        return result

    def get_job(self, job_id: str) -> dict | None:
        return self.artifact_store.get_job(job_id)

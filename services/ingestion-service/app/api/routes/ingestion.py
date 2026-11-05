from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.domain.models import Provider
from app.services.ingestion_service import IngestionService
from app.infrastructure.local_artifact_store import LocalArtifactStore

router = APIRouter(tags=["ingestion"])

MAX_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}
service = IngestionService(artifact_store=LocalArtifactStore())


@router.post("/ingestion/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_ingestion_job(
    file: Annotated[UploadFile, File()],
    provider: Annotated[Provider, Form()],
    service_name: Annotated[str, Form(min_length=1, max_length=120)],
    source_url: Annotated[str, Form(min_length=8, max_length=2048)],
) -> dict:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only HTML documents are supported.")

    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MiB MVP limit.")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if not source_url.startswith(("https://", "http://")):
        raise HTTPException(status_code=422, detail="source_url must be an HTTP(S) URL.")

    try:
        result = service.process(
            raw_bytes=content,
            filename=file.filename or "document.html",
            provider=provider,
            service_name=service_name.strip(),
            source_url=source_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result


@router.get("/ingestion/jobs/{job_id}")
def get_ingestion_job(job_id: str) -> dict:
    result = service.get_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Ingestion job not found.")
    return result

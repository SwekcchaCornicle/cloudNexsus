from fastapi import APIRouter, HTTPException
from app.config import settings
from app.domain.schemas import IngestionArtifact
from app.infrastructure.providers import build_providers
from app.infrastructure.artifact_store import LocalArtifactStore
from app.services.extraction_service import ExtractionService

router = APIRouter(tags=["extractions"])
embedding_provider, knowledge_extractor = build_providers(settings)
service = ExtractionService(embedding_provider, knowledge_extractor, LocalArtifactStore(settings.app_data_dir))

@router.post("/extractions")
def create_extraction(artifact: IngestionArtifact):
    try:
        return service.process(artifact)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Extraction provider failed; check service logs and configuration.") from exc

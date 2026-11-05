"""HTTP boundary: validate request, call orchestrator, translate failures safely."""
import logging

from fastapi import APIRouter, HTTPException, Request
from neo4j.exceptions import Neo4jError
from app.domain.schemas import RetrievalRequest, RetrievalResponse

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])
logger = logging.getLogger(__name__)

@router.post("/query", response_model=RetrievalResponse)
def retrieve_query(payload: RetrievalRequest, request: Request) -> RetrievalResponse:
    """Return evidence/context for a question; this endpoint does not compose an answer."""
    try:
        return request.app.state.retrieval_service.retrieve(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Neo4jError as exc:
        logger.exception("Neo4j retrieval failed")
        # Avoid leaking database credentials or connection details to API consumers.
        raise HTTPException(status_code=503, detail="Neo4j retrieval failed; check index/config.") from exc
    except Exception as exc:
        logger.exception("Retrieval operation failed")
        raise HTTPException(status_code=502, detail="Retrieval operation failed.") from exc

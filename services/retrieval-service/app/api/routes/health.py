"""Liveness route; deliberately does not call paid services."""
from fastapi import APIRouter
router = APIRouter(tags=["Health"])

@router.get("/health")
def health():
    return {"status": "ok", "service": "cloudnexus-retrieval"}

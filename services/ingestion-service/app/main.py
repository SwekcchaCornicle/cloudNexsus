from fastapi import FastAPI

from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.health import router as health_router

app = FastAPI(
    title="CloudNexus Ingestion Service",
    version="0.1.0",
    description="Ingest and normalize multi-cloud documentation HTML.",
)

app.include_router(health_router)
app.include_router(ingestion_router, prefix="/api/v1")

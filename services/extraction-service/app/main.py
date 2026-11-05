from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.extractions import router as extraction_router

app = FastAPI(title="CloudNexus Extraction Service", version="0.1.0")
app.include_router(health_router)
app.include_router(extraction_router, prefix="/api/v1")

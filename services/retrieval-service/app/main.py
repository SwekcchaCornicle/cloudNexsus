"""Application composition root: build shared adapters once and close them cleanly."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings

from app.infrastructure.embedding_client import VertexEmbeddingClient
from app.infrastructure.neo4j_client import Neo4jClient
from app.infrastructure.vector_retriever import Neo4jVectorRetriever
from app.infrastructure.bm25_retriever import Neo4jBM25Retriever
from app.infrastructure.graph_retriever import Neo4jGraphRetriever

from app.services.retrieval_service import RetrievalService

from app.api.routes.health import router as health_router
from app.api.routes.retrieval import router as retrieval_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize clients at startup and close them cleanly."""

    settings = get_settings()
    settings.validate_runtime()

    # 1. Initialize query embedding client.
    embedding = VertexEmbeddingClient(
        settings.gcp_project_id,
        settings.gcp_region,
        settings.vertex_embedding_model,
        settings.embedding_dimensions,
    )

    # 2. Initialize Neo4j connection.
    neo4j = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )

    # 3. Validate database connectivity.
    neo4j.verify_connectivity()

    # 4. Initialize individual retrieval components.
    vector_retriever = Neo4jVectorRetriever(
        neo4j,
        settings.vector_index_name,
    )

    bm25_retriever = Neo4jBM25Retriever(
        neo4j,
        index_name="chunk_content_fulltext",
    )

    graph_retriever = Neo4jGraphRetriever(neo4j)

    # 5. Initialize hybrid retrieval service.
    app.state.retrieval_service = RetrievalService(
        embedding,
        vector_retriever,
        bm25_retriever,
        graph_retriever,
    )

    yield

    # 6. Close database connection.
    neo4j.close()


app = FastAPI(
    title="CloudNexus Retrieval Service",
    version="0.1.0",
    description="Hybrid semantic, keyword and knowledge-graph retrieval.",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(retrieval_router, prefix="/api/v1")
# CloudNexus Extraction Service — Vertex-enabled

This is the existing CloudNexus extraction service, updated to support Google Vertex AI while preserving its original ingestion Pydantic contract and optional AWS Bedrock adapters.

## Modes
- `local`: deterministic test mocks; local vectors are not semantic embeddings.
- `vertex`: Gemini Flash extraction + Gemini Embedding 001 using Application Default Credentials (ADC).
- `aws`: optional Bedrock adapters retained for later comparison.

## Windows CMD setup
```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```
Authenticate without putting tokens in `.env`:
```cmd
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_EXACT_PROJECT_ID
gcloud auth application-default set-quota-project YOUR_EXACT_PROJECT_ID
```
Enable Vertex AI API and grant Vertex AI User (`roles/aiplatform.user`). Quota project usage may also require Service Usage Consumer. Use the exact project ID shown by `gcloud projects list`; in the earlier terminal output it appeared as `cloudnexsus`, but verify before configuring.

Set `.env` for Vertex:
```env
EXTRACTION_MODE=vertex
GCP_PROJECT_ID=YOUR_EXACT_PROJECT_ID
GCP_REGION=global
VERTEX_CHAT_MODEL=gemini-3.8-flash
VERTEX_EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=1024
APP_DATA_DIR=data
```
Model availability and location requirements can change; verify them for your project before deployment.

## Run
```cmd
pytest -v
uvicorn app.main:app --reload --port 8001
```
Swagger: http://127.0.0.1:8001/docs

## Processing flow
`Uvicorn -> app.main -> extraction route -> Pydantic IngestionArtifact -> build_providers -> ExtractionService.process -> embed + extract -> evidence validation -> LocalArtifactStore.save`.

- `build_providers(settings)`: selects local, AWS, or Vertex strategy.
- `VertexEmbeddingProvider.embed(text)`: requests a vector and checks dimensions.
- `VertexKnowledgeExtractor.extract(...)`: requests schema-shaped JSON and validates it with Pydantic.
- `ExtractionService.process(artifact)`: coordinates both AI tasks for every chunk.
- `LocalArtifactStore.save(...)`: writes `data/extracted/<document_id>/extraction.json`.

## Production boundaries
This service currently writes to local disk, not S3, and does not persist to Neo4j/PostgreSQL. Durable async jobs, retries/backoff, bounded concurrency, idempotency, cost budgets, canonical entity resolution, full ontology checks, and observability remain future work. Do not mix local mock vectors with Vertex vectors in a production vector index. Vertex calls may incur charges.

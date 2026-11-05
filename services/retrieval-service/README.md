# CloudNexus Retrieval Service

FastAPI microservice for retrieving documentation context from the Neo4j graph built by the CloudNexus Extraction Service.

## Workflow
1. Validate a user's question.
2. Embed it with Vertex AI `gemini-embedding-001` (1,024 dimensions).
3. Search Neo4j vector index `chunk_embedding_index`.
4. Enrich matching chunks with graph relationships.
5. Apply a transparent lexical/semantic baseline reranker.
6. Return source chunks and graph facts. This service does not generate the final answer.

## Expected graph contract
`(Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)`
`(Entity)-[:RELATED_TO]->(Entity)`

Expected chunk properties: `content`, `provider`, `service_name`, `source_url`, `document_id`, `embedding_model`, `embedding`.
Expected entity properties: `name`, `canonical_name`, `provider`.
Expected relationship properties: `predicate`, `evidence`, `confidence`.

**Important:** Confirm these names against the actual `GraphRepository` in Extraction Service. Update Cypher if your persisted schema differs. The vector index must target `Chunk.embedding`, 1,024 dimensions, and be ONLINE.

## Windows CMD setup
```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env
gcloud auth application-default login
uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8002
```
Swagger: http://127.0.0.1:8002/docs

## Request
`POST /api/v1/retrieval/query`
```json
{"question":"How can AWS Lambda read objects from S3 securely?","provider":"AWS","top_k":5}
```

## Tests
`pytest`

Tests mock external services; they do not require cloud credentials.

## Troubleshooting
- **Index missing/offline:** Run `SHOW VECTOR INDEXES` in Neo4j Browser.
- **No results:** Ensure extraction JSON was imported into Neo4j. The extraction API writes JSON; a separate import step persists it.
- **Dimension mismatch:** Query and document embeddings must both be 1,024 dimensions and use a compatible embedding model. Never mix local mock vectors with Vertex vectors.
- **Credentials:** Keep `.env` local and out of Git. Use ADC for Vertex and preferably a read-only Neo4j account for this service.

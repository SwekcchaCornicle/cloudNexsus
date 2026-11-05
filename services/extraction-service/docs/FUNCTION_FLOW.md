# Function flow and interview guide

1. `app.main` creates FastAPI and mounts route modules.
2. `config.settings` reads `.env` once at startup.
3. `build_providers(settings)` selects local, Bedrock, or Vertex adapters.
4. FastAPI/Pydantic validates the incoming `IngestionArtifact` before route execution.
5. `ExtractionService.process()` iterates document chunks.
6. `embedding_provider.embed()` creates a vector for semantic retrieval.
7. `knowledge_extractor.extract()` returns entities and graph relationships.
8. The service checks relationship evidence against the original chunk.
9. `LocalArtifactStore.save()` writes the completed JSON artifact.

| Function | Input | Output | Purpose |
|---|---|---|---|
| `build_providers` | Settings | Provider adapters | Strategy selection |
| `embed` | Chunk text | Float vector | Semantic retrieval |
| `extract` | Text/provider/service | KnowledgeExtraction | Graph facts |
| `process` | IngestionArtifact | Summary/path | Use-case orchestration |
| `save` | ExtractionArtifact | File path | Persistence |

## Interview concepts
- Strategy Pattern: local, AWS and Vertex adapters can be swapped.
- Dependency Injection: the service receives adapters rather than creating cloud clients itself.
- Separation of concerns: API, schemas, orchestration, provider calls and persistence are isolated.
- Provenance: relationships carry source evidence that is checked before persistence.

## Production backlog
Retries/backoff, bounded concurrency, idempotency, durable job status, token/cost budgets, canonical entity resolution, ontology checks, S3 persistence, Neo4j graph/vector persistence, observability, and evaluation for precision/recall/evidence accuracy/latency/cost.

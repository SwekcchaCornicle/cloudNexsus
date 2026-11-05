# Function flow and learning notes

- `api/routes/retrieval.py::retrieve_query`: HTTP entry point; Pydantic validates JSON and the route calls the orchestrator.
- `services/retrieval_service.py::retrieve`: coordinates the full workflow and converts database rows into response models.
- `infrastructure/embedding_client.py::embed_query`: embeds the user's question with Vertex AI. This must match the extraction embedding model and dimensions.
- `infrastructure/vector_retriever.py::search`: calls Neo4j's vector index and returns the most similar Chunk nodes.
- `infrastructure/graph_retriever.py::relationships_for_chunk`: follows graph edges to retrieve connected entities and relationship evidence.
- `services/reranker.py`: combines vector similarity (85%) and lexical overlap (15%). This is a simple baseline, not an ML reranker.
- `main.py::lifespan`: creates shared clients once at startup and closes Neo4j on shutdown.

## Why embedding the question?
The extracted documentation chunks already have vectors. The user's question must be converted into a vector in the same embedding space so nearest-neighbour similarity can find relevant chunks.

## Why vector + graph?
Vector search finds semantically relevant text. Graph traversal adds explicit relationships between concepts. Together they provide richer context to a later answer-generation service.

## Scope boundary
Retrieval returns evidence. A future Answer Generation service will use the retrieved evidence to write the final answer. This service does not call Gemini for answer composition.


"""
CloudNexus Neo4j vector search.

Responsibilities:
1. Validate incoming query embeddings.
2. Search the Neo4j vector index.
3. Retrieve the matching documentation chunks.
4. Return source metadata and similarity scores.

This module does not generate embeddings.
Gemini question embedding will be connected in the next step.
"""

import math


class VectorSearch:
    """Search CloudNexus documentation using vector similarity."""

    def __init__(self, neo4j_client):
        self.client = neo4j_client
        self.index_name = "chunk_embedding_index"
        self.embedding_dimensions = 1024

    def _validate_embedding(self, embedding):
        """Ensure the query vector matches the indexed vector format."""

        if not isinstance(embedding, list):
            raise ValueError("Query embedding must be a list")

        if len(embedding) != self.embedding_dimensions:
            raise ValueError(
                f"Expected {self.embedding_dimensions} dimensions, "
                f"received {len(embedding)}"
            )

        for value in embedding:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Embedding contains invalid numeric values")

    def search(self, query_embedding, top_k=5, provider=None):
        """
        Retrieve the most similar documentation chunks.

        Args:
            query_embedding: 1024-dimensional Gemini embedding.
            top_k: Maximum number of results.
            provider: Optional provider filter (AWS, AZURE, GCP).

        Returns:
            List of matching chunks with metadata and similarity scores.
        """

        self._validate_embedding(query_embedding)

        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ValueError("top_k must be an integer")

        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        if provider is not None:
            provider = provider.strip().upper()

            if provider not in {"AWS", "AZURE", "GCP"}:
                raise ValueError("Unsupported provider")

        query = """
        CALL db.index.vector.queryNodes(
            $index_name,
            $top_k,
            $query_embedding
        )
        YIELD node, score

        MATCH (d:Document)-[:HAS_CHUNK]->(node)

        WHERE $provider IS NULL OR d.provider = $provider

        OPTIONAL MATCH (node)-[:MENTIONS]->(e:Entity)

        RETURN
            node.chunk_id AS chunk_id,
            node.content AS content,
            node.provider AS provider,
            node.service_name AS service_name,
            node.source_url AS source_url,
            node.embedding_model_id AS embedding_model_id,
            d.document_id AS document_id,
            d.title AS document_title,
            collect(DISTINCT {
                name: e.name,
                canonical_name: e.canonical_name,
                entity_type: e.entity_type
            }) AS entities,
            score AS similarity_score

        ORDER BY similarity_score DESC
        """

        return self.client.execute_read(
            query,
            {
                "index_name": self.index_name,
                "top_k": top_k,
                "query_embedding": query_embedding,
                "provider": provider,
            },
        )

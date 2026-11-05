
"""
CloudNexus question embedding service.

Responsibilities:
1. Reuse the existing embedding provider factory.
2. Generate embeddings for natural-language questions.
3. Validate the returned vector.
4. Ensure dimensions match the Neo4j vector index.

The service does not connect to Neo4j.
"""

import math

from app.config import settings
from app.infrastructure.providers import build_providers


class EmbeddingService:
    """Generates semantic embeddings for user questions."""

    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider
        self.dimensions = settings.embedding_dimensions

    @classmethod
    def from_settings(cls):
        """
        Build the configured provider using the existing factory.

        The factory returns both an embedding provider and a
        knowledge extractor. We only need the embedding provider here.
        """

        if settings.extraction_mode != "vertex":
            raise ValueError(
                "Question embedding currently requires "
                "EXTRACTION_MODE=vertex."
            )

        embedding_provider, _ = build_providers(settings)

        return cls(embedding_provider)

    def embed_question(self, question):
        """Convert a natural-language question into a numeric vector."""

        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

        vector = self.embedding_provider.embed(question.strip())

        if not isinstance(vector, list):
            raise ValueError("Embedding provider must return a list.")

        if len(vector) != self.dimensions:
            raise ValueError(
                f"Expected {self.dimensions} dimensions, "
                f"received {len(vector)}."
            )

        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in vector
        ):
            raise ValueError("Embedding contains invalid numeric values.")

        return [float(value) for value in vector]

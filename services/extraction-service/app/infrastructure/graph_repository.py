
"""
CloudNexus Graph Repository.

Persists one extraction artifact into Neo4j.

Graph structure:
    (Document)-[:HAS_CHUNK]->(Chunk)
    (Chunk)-[:MENTIONS]->(Entity)
    (Entity)-[:RELATED_TO]->(Entity)

Important:
- Uses MERGE to make repeated imports idempotent.
- Uses canonical entity identities.
- Preserves source evidence and confidence.
- Uses one transaction per artifact.
- Validates embeddings and relationship endpoints before writing.
"""

import math

from neo4j import Transaction


class GraphRepository:
    """Persists extracted cloud documentation into Neo4j."""

    def __init__(self, neo4j_client):
        self.client = neo4j_client
        self.embedding_dimensions = 1024

    @staticmethod
    def _normalize(value):
        """Normalize names for case-insensitive entity lookup."""
        return value.strip().casefold()

    def _validate_artifact(self, artifact):
        """Validate the artifact before opening a database transaction."""

        required_fields = [
            "document_id",
            "provider",
            "title",
            "source_url",
            "chunks",
        ]

        for field in required_fields:
            if field not in artifact:
                raise ValueError(f"Artifact is missing field: {field}")

        if not isinstance(artifact["chunks"], list):
            raise ValueError("Artifact chunks must be a list")

        if artifact.get("chunk_count") != len(artifact["chunks"]):
            raise ValueError("chunk_count does not match actual chunks")

        for chunk in artifact["chunks"]:
            if chunk.get("document_id") != artifact["document_id"]:
                raise ValueError(
                    f"Chunk {chunk.get('chunk_id')} belongs to another document"
                )

            embedding = chunk.get("embedding")

            if not isinstance(embedding, list):
                raise ValueError("Chunk embedding must be a list")

            if len(embedding) != self.embedding_dimensions:
                raise ValueError(
                    f"Expected {self.embedding_dimensions} embedding values; "
                    f"received {len(embedding)}"
                )

            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in embedding
            ):
                raise ValueError("Embedding contains invalid numeric values")

    def _persist_transaction(self, tx: Transaction, artifact):
        """
        Write the entire artifact inside one Neo4j transaction.

        If any validation or database operation fails, Neo4j rolls
        back the transaction.
        """

        document_id = artifact["document_id"]
        provider = artifact["provider"]

        # 1. Create or reuse the document node.
        tx.run(
            """
            MERGE (d:Document {document_id: $document_id})
            SET d.provider = $provider,
                d.title = $title,
                d.source_url = $source_url,
                d.extraction_mode = $extraction_mode,
                d.chunk_count = $chunk_count
            """,
            document_id=document_id,
            provider=provider,
            title=artifact["title"],
            source_url=artifact["source_url"],
            extraction_mode=artifact.get("extraction_mode"),
            chunk_count=artifact["chunk_count"],
        ).consume()

        # 2. Process every extracted chunk.
        for chunk in artifact["chunks"]:

            chunk_id = chunk["chunk_id"]
            chunk_provider = chunk.get("provider", provider)

            tx.run(
                """
                MATCH (d:Document {document_id: $document_id})

                MERGE (c:Chunk {chunk_id: $chunk_id})
                SET c.document_id = $document_id,
                    c.provider = $provider,
                    c.service_name = $service_name,
                    c.source_url = $source_url,
                    c.heading_path = $heading_path,
                    c.content = $content,
                    c.embedding = $embedding,
                    c.embedding_model_id = $embedding_model_id

                MERGE (d)-[:HAS_CHUNK]->(c)
                """,
                document_id=document_id,
                chunk_id=chunk_id,
                provider=chunk_provider,
                service_name=chunk.get("service_name"),
                source_url=chunk.get("source_url"),
                heading_path=chunk.get("heading_path"),
                content=chunk["content"],
                embedding=chunk["embedding"],
                embedding_model_id=chunk.get("embedding_model_id"),
            ).consume()

            extraction = chunk.get("extraction", {})
            entities = extraction.get("entities", [])
            relationships = extraction.get("relationships", [])

            # Map both display names and canonical names to one identity.
            entity_lookup = {}

            # 3. Create or reuse entity nodes.
            for entity in entities:

                name = entity["name"]
                canonical_name = entity["canonical_name"]
                entity_provider = entity.get("provider", chunk_provider)

                if not name.strip() or not canonical_name.strip():
                    raise ValueError("Entity name and canonical_name are required")

                if entity_provider != chunk_provider:
                    raise ValueError(
                        f"Entity provider mismatch for {name}: "
                        f"{entity_provider} != {chunk_provider}"
                    )

                identity = (
                    entity_provider,
                    canonical_name,
                )

                for alias in (name, canonical_name):
                    normalized = self._normalize(alias)

                    existing = entity_lookup.get(normalized)

                    if existing is not None and existing != identity:
                        raise ValueError(
                            f"Ambiguous entity name: {alias}"
                        )

                    entity_lookup[normalized] = identity

                tx.run(
                    """
                    MATCH (c:Chunk {chunk_id: $chunk_id})

                    MERGE (e:Entity {
                        provider: $provider,
                        canonical_name: $canonical_name
                    })

                    SET e.name = $name,
                        e.entity_type = $entity_type,
                        e.description = $description

                    MERGE (c)-[:MENTIONS]->(e)
                    """,
                    chunk_id=chunk_id,
                    provider=entity_provider,
                    canonical_name=canonical_name,
                    name=name,
                    entity_type=entity.get("entity_type"),
                    description=entity.get("description"),
                ).consume()

            # 4. Create relationships between resolved entities.
            for relationship in relationships:

                source_name = relationship["source_entity"]
                target_name = relationship["target_entity"]

                source_identity = entity_lookup.get(
                    self._normalize(source_name)
                )
                target_identity = entity_lookup.get(
                    self._normalize(target_name)
                )

                if source_identity is None or target_identity is None:
                    raise ValueError(
                        "Relationship endpoint could not be resolved: "
                        f"{source_name} -> {target_name}"
                    )

                confidence = float(relationship["confidence"])

                if not 0.0 <= confidence <= 1.0:
                    raise ValueError(
                        f"Invalid relationship confidence: {confidence}"
                    )

                predicate = relationship["predicate"]
                evidence = relationship["evidence"]

                tx.run(
                    """
                    MATCH (source:Entity {
                        provider: $source_provider,
                        canonical_name: $source_canonical
                    })

                    MATCH (target:Entity {
                        provider: $target_provider,
                        canonical_name: $target_canonical
                    })

                    MERGE (source)-[r:RELATED_TO {
                        predicate: $predicate,
                        source_chunk_id: $chunk_id
                    }]->(target)

                    SET r.evidence = $evidence,
                        r.confidence = $confidence
                    """,
                    source_provider=source_identity[0],
                    source_canonical=source_identity[1],
                    target_provider=target_identity[0],
                    target_canonical=target_identity[1],
                    predicate=predicate,
                    chunk_id=chunk_id,
                    evidence=evidence,
                    confidence=confidence,
                ).consume()

        return {
            "document_id": document_id,
            "chunks": len(artifact["chunks"]),
            "status": "COMPLETED",
        }

    def persist_artifact(self, artifact):
        """Validate and persist one complete extraction artifact."""

        self._validate_artifact(artifact)

        with self.client.driver.session(
            database=self.client.database
        ) as session:
            return session.execute_write(
                self._persist_transaction,
                artifact,
            )

"""Neo4j persistence and retrieval adapters for CloudNexus."""

import math


class GraphRepository:
    """Persist extraction artifacts as an idempotent Neo4j knowledge graph.

    Graph shape:
        (Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)
        (Entity)-[:RELATED_TO]->(Entity)

    Entity identity is scoped by provider and canonical_name. Relationship
    identity is scoped by predicate and the source chunk so evidence from
    different documentation chunks is retained independently.
    """

    EMBEDDING_DIMENSIONS = 1024

    def __init__(self, neo4j_client):
        self.neo4j = neo4j_client

    @staticmethod
    def _normalise_entity_key(value):
        return " ".join(str(value).strip().casefold().split())

    @staticmethod
    def _required(value, field_name):
        if value is None or value == "":
            raise ValueError(f"Artifact is missing required field: {field_name}")
        return value

    def persist_artifact(self, artifact):
        """Validate and persist one serialized ExtractionArtifact.

        The writes use MERGE and are safe to retry after partial failures.
        """
        if not isinstance(artifact, dict):
            raise TypeError("artifact must be a dictionary.")

        document_id = self._required(
            artifact.get("document_id"), "document_id"
        )
        provider = self._required(artifact.get("provider"), "provider")
        chunks = artifact.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ValueError("Artifact must contain at least one chunk.")

        document = {
            "document_id": document_id,
            "provider": str(provider),
            "title": artifact.get("title", ""),
            "source_url": artifact.get("source_url", ""),
            "extraction_mode": artifact.get("extraction_mode", ""),
            "chunk_count": len(chunks),
        }

        chunk_rows = []
        entity_rows = []
        relationship_rows = []

        for chunk in chunks:
            chunk_id = self._required(chunk.get("chunk_id"), "chunk_id")
            if chunk.get("document_id") != document_id:
                raise ValueError(
                    f"Chunk {chunk_id} belongs to a different document."
                )

            embedding = chunk.get("embedding")
            if not isinstance(embedding, list):
                raise ValueError(f"Chunk {chunk_id} has no embedding list.")
            if len(embedding) != self.EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Chunk {chunk_id} embedding must contain "
                    f"{self.EMBEDDING_DIMENSIONS} dimensions; "
                    f"received {len(embedding)}."
                )
            if any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                for value in embedding
            ):
                raise ValueError(
                    f"Chunk {chunk_id} embedding contains a non-finite "
                    "or non-numeric value."
                )

            chunk_rows.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "provider": str(chunk.get("provider", provider)),
                "service_name": chunk.get("service_name", ""),
                "source_url": chunk.get("source_url", ""),
                "heading_path": chunk.get("heading_path", []),
                "content": self._required(chunk.get("content"), "content"),
                "embedding": [float(value) for value in embedding],
                "embedding_model_id": self._required(
                    chunk.get("embedding_model_id"), "embedding_model_id"
                ),
            })

            extraction = chunk.get("extraction") or {}
            entities = extraction.get("entities") or []
            relationships = extraction.get("relationships") or []
            entity_lookup = {}

            for entity in entities:
                name = self._required(entity.get("name"), "entity.name")
                canonical_name = self._required(
                    entity.get("canonical_name"), "entity.canonical_name"
                )
                entity_provider = str(entity.get("provider") or provider)
                row = {
                    "chunk_id": chunk_id,
                    "provider": entity_provider,
                    "name": name,
                    "canonical_name": canonical_name,
                    "entity_type": entity.get("entity_type", "UNKNOWN"),
                    "description": entity.get("description", ""),
                }
                entity_rows.append(row)
                entity_lookup[self._normalise_entity_key(name)] = row
                entity_lookup[
                    self._normalise_entity_key(canonical_name)
                ] = row

            for relationship in relationships:
                source_name = self._required(
                    relationship.get("source_entity"),
                    "relationship.source_entity",
                )
                target_name = self._required(
                    relationship.get("target_entity"),
                    "relationship.target_entity",
                )
                source = entity_lookup.get(
                    self._normalise_entity_key(source_name)
                )
                target = entity_lookup.get(
                    self._normalise_entity_key(target_name)
                )
                if source is None or target is None:
                    raise ValueError(
                        f"Relationship in chunk {chunk_id} references an "
                        "entity that is not present in that chunk: "
                        f"{source_name!r} -> {target_name!r}."
                    )

                relationship_rows.append({
                    "provider": str(chunk.get("provider", provider)),
                    "source_canonical_name": source["canonical_name"],
                    "target_canonical_name": target["canonical_name"],
                    "predicate": self._required(
                        relationship.get("predicate"),
                        "relationship.predicate",
                    ),
                    "evidence": relationship.get("evidence", ""),
                    "confidence": float(relationship.get("confidence", 0.0)),
                    "source_chunk_id": chunk_id,
                })

        # 1. Create/update the document.
        self.neo4j.execute_write(
            """
            MERGE (d:Document {document_id: $document_id})
            SET d.provider = $provider,
                d.title = $title,
                d.source_url = $source_url,
                d.extraction_mode = $extraction_mode,
                d.chunk_count = $chunk_count
            RETURN d.document_id AS document_id
            """,
            document,
        )

        # 2. Create/update chunks and connect them to their document.
        self.neo4j.execute_write(
            """
            MATCH (d:Document {document_id: $document_id})
            UNWIND $rows AS row
            MERGE (c:Chunk {chunk_id: row.chunk_id})
            SET c.document_id = row.document_id,
                c.provider = row.provider,
                c.service_name = row.service_name,
                c.source_url = row.source_url,
                c.heading_path = row.heading_path,
                c.content = row.content,
                c.embedding = row.embedding,
                c.embedding_model_id = row.embedding_model_id
            MERGE (d)-[:HAS_CHUNK]->(c)
            RETURN count(c) AS chunks_written
            """,
            {"document_id": document_id, "rows": chunk_rows},
        )

        # 3. Create/update entities and link each one to the chunk that
        #    supplied its mention.
        if entity_rows:
            self.neo4j.execute_write(
                """
                UNWIND $rows AS row
                MATCH (c:Chunk {chunk_id: row.chunk_id})
                MERGE (e:Entity {
                    provider: row.provider,
                    canonical_name: row.canonical_name
                })
                SET e.name = row.name,
                    e.entity_type = row.entity_type,
                    e.description = row.description
                MERGE (c)-[:MENTIONS]->(e)
                RETURN count(e) AS entities_written
                """,
                {"rows": entity_rows},
            )

        # 4. Persist evidence-backed relationships between entities.
        if relationship_rows:
            self.neo4j.execute_write(
                """
                UNWIND $rows AS row
                MATCH (source:Entity {
                    provider: row.provider,
                    canonical_name: row.source_canonical_name
                })
                MATCH (target:Entity {
                    provider: row.provider,
                    canonical_name: row.target_canonical_name
                })
                MERGE (source)-[r:RELATED_TO {
                    predicate: row.predicate,
                    source_chunk_id: row.source_chunk_id
                }]->(target)
                SET r.evidence = row.evidence,
                    r.confidence = row.confidence
                RETURN count(r) AS relationships_written
                """,
                {"rows": relationship_rows},
            )

        return {
            "document_id": document_id,
            "chunks_written": len(chunk_rows),
            "entities_written": len(entity_rows),
            "relationships_written": len(relationship_rows),
            "embedding_dimensions": self.EMBEDDING_DIMENSIONS,
            "idempotent": True,
        }


class Neo4jVectorRetriever:
    """Search documentation chunks using the configured Neo4j vector index."""

    def __init__(self, neo4j_client, index_name):
        self.neo4j = neo4j_client
        self.index_name = index_name

    def search(self, query_embedding, top_k, provider=None, service_name=None):
        """Retrieve relevant chunks and their connected entities."""
        if not self.index_name.replace("_", "").isalnum():
            raise ValueError("Unsafe VECTOR_INDEX_NAME.")

        query = f"""
        CALL db.index.vector.queryNodes(
            $index_name,
            $top_k,
            $query_embedding
        )
        YIELD node AS chunk, score

        WHERE ($provider IS NULL
               OR toUpper(chunk.provider) = $provider)

          AND ($service_name IS NULL
               OR toLower(chunk.service_name) = toLower($service_name))

        OPTIONAL MATCH (chunk)-[:MENTIONS]->(entity:Entity)

        RETURN
            chunk.chunk_id AS chunk_id,
            chunk.content AS content,
            score AS score,
            chunk.provider AS provider,
            chunk.service_name AS service_name,
            chunk.source_url AS source_url,
            chunk.document_id AS document_id,
            chunk.embedding_model_id AS embedding_model,
            collect(DISTINCT {{
                name: entity.name,
                canonical_name: entity.canonical_name,
                provider: entity.provider
            }}) AS entities

        ORDER BY score DESC
        LIMIT $top_k
        """

        records = self.neo4j.execute_read(
            query,
            {
                "index_name": self.index_name,
                "top_k": top_k,
                "query_embedding": query_embedding,
                "provider": provider.upper() if provider else None,
                "service_name": service_name,
            },
        )
        return [record.data() if hasattr(record, "data") else record for record in records]

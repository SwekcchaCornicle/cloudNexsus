
"""
CloudNexus graph persistence integration test.

Reads the existing Azure extraction artifact,
persists it into Neo4j, and verifies the saved graph.
"""

import json
from pathlib import Path

from app.infrastructure.neo4j_client import Neo4jClient
from app.infrastructure.graph_repository import GraphRepository


ARTIFACT_PATH = Path(
    "data/extracted/"
    "85d639fb-d7ef-48fb-b650-616c4149686d/"
    "extraction.json"
)


def main():
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(ARTIFACT_PATH)

    # Load the actual Vertex AI extraction output.
    with ARTIFACT_PATH.open("r", encoding="utf-8") as file:
        artifact = json.load(file)

    client = Neo4jClient()

    try:
        client.verify_connection()

        repository = GraphRepository(client)

        # Persist the complete artifact in one transaction.
        result = repository.persist_artifact(artifact)
        print("PERSISTENCE RESULT:", result)

        document_id = artifact["document_id"]

        # Verify document and chunk count.
        graph_counts = client.execute_read(
            """
            MATCH (d:Document {document_id: $document_id})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            RETURN count(DISTINCT c) AS chunks
            """,
            {"document_id": document_id},
        )

        # Verify entities mentioned by this document.
        entity_counts = client.execute_read(
            """
            MATCH (d:Document {document_id: $document_id})
                  -[:HAS_CHUNK]->(c:Chunk)
                  -[:MENTIONS]->(e:Entity)
            RETURN count(DISTINCT e) AS entities
            """,
            {"document_id": document_id},
        )

        # Verify relationships originating from its chunks.
        relationship_counts = client.execute_read(
            """
            MATCH (d:Document {document_id: $document_id})
                  -[:HAS_CHUNK]->(c:Chunk)
            WITH collect(c.chunk_id) AS chunk_ids
            MATCH ()-[r:RELATED_TO]->()
            WHERE r.source_chunk_id IN chunk_ids
            RETURN count(r) AS relationships
            """,
            {"document_id": document_id},
        )

        print("VERIFICATION:")
        print("Chunks:", graph_counts[0]["chunks"])
        print("Entities:", entity_counts[0]["entities"])
        print("Relationships:", relationship_counts[0]["relationships"])

    finally:
        client.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    main()

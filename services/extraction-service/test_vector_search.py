
"""
CloudNexus vector search integration test.

Uses an existing stored Azure embedding as the query vector.
This tests Neo4j vector retrieval without making a Gemini API call.
"""

from app.infrastructure.neo4j_client import Neo4jClient
from app.infrastructure.vector_search import VectorSearch


AZURE_DOCUMENT_ID = "85d639fb-d7ef-48fb-b650-616c4149686d"


def main():
    client = Neo4jClient()

    try:
        client.verify_connection()
        print("Neo4j connection successful.")

        # Retrieve one real embedding already stored in Neo4j.
        stored_vectors = client.execute_read(
            """
            MATCH (d:Document {document_id: $document_id})
                  -[:HAS_CHUNK]->(c:Chunk)
            RETURN c.embedding AS embedding
            LIMIT 1
            """,
            {"document_id": AZURE_DOCUMENT_ID},
        )

        if not stored_vectors:
            raise RuntimeError("No stored Azure embedding found.")

        query_embedding = stored_vectors[0]["embedding"]

        print("Query vector dimensions:", len(query_embedding))

        # Search the vector index using the stored embedding.
        vector_search = VectorSearch(client)

        results = vector_search.search(
            query_embedding=query_embedding,
            top_k=3,
        )

        print("\nVECTOR SEARCH RESULTS")
        print("Number of results:", len(results))

        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Provider:", result["provider"])
            print("Document:", result["document_title"])
            print("Chunk ID:", result["chunk_id"])
            print("Similarity:", result["similarity_score"])
            print("Content:", result["content"][:250])
            print("Entities:", result["entities"])

        # The query vector came from the Azure chunk itself.
        if not any(
            result["chunk_id"].startswith(AZURE_DOCUMENT_ID)
            for result in results
        ):
            raise AssertionError(
                "Expected Azure source chunk was not retrieved."
            )

        print("\nCloudNexus vector search test PASSED.")

    finally:
        client.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    main()


from app.config import get_settings
from app.infrastructure.bm25_retriever import Neo4jBM25Retriever
from app.infrastructure.neo4j_client import Neo4jClient


def main():
    settings = get_settings()
    client = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )

    try:
        client.verify_connectivity()
        print("Neo4j connection successful.")

        # Initialize our new keyword retriever.
        retriever = Neo4jBM25Retriever(client)

        # Search for an exact AWS technical concept.
        results = retriever.search(
            question="event source mapping Lambda function",
            top_k=5,
            provider="AWS",
        )

        print("\nBM25 Search Results:")
        print("=" * 60)

        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Chunk ID:", result["chunk_id"])
            print("Score:", result["score"])
            print("Provider:", result["provider"])
            print("Content:", result["content"])
            print("Source:", result["source_url"])

        print("\nTotal results:", len(results))

    finally:
        # Always close the database connection.
        client.close()


if __name__ == "__main__":
    main()

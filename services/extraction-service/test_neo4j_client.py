
from app.infrastructure.neo4j_client import Neo4jClient


def main():
    client = Neo4jClient()

    try:
        client.verify_connection()
        print("CloudNexus Neo4jClient connection successful!")

        result = client.execute_read(
            "RETURN 'CloudNexus' AS project, 1024 AS embedding_dimensions"
        )

        print("Cypher result:", result)

    finally:
        client.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    main()

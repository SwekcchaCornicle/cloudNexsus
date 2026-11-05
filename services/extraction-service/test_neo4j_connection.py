
"""
CloudNexus - Neo4j connectivity test.

Purpose:
1. Load Neo4j credentials from the local .env file.
2. Create a secure connection to Neo4j AuraDB.
3. Verify that the database is reachable.
4. Execute a simple Cypher query.
5. Close the connection cleanly.

This test does not create or modify database data.
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load environment variables from the .env file
load_dotenv()

# Read connection settings
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def test_connection():
    """Connect to AuraDB and execute a read-only test query."""

    # Validate configuration before attempting a connection
    required_settings = {
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
    }

    missing = [
        key for key, value in required_settings.items()
        if not value
    ]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    driver = None

    try:
        print("Connecting to Neo4j AuraDB...")

        # Create the Neo4j driver
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        )

        # Verify network connectivity and authentication
        driver.verify_connectivity()
        print("Connection and authentication successful!")

        # Open a session against the configured database
        with driver.session(database=NEO4J_DATABASE) as session:

            # Execute a harmless read-only Cypher query
            result = session.run("RETURN 1 AS connection_test")
            record = result.single()

            if record["connection_test"] != 1:
                raise RuntimeError("Unexpected database test result")

            print(f"Database: {NEO4J_DATABASE}")
            print("Cypher query executed successfully!")

        print("CloudNexus -> Neo4j AuraDB connection test PASSED.")

    except Exception as error:
        print(f"Neo4j connection test FAILED: {error}")
        raise

    finally:
        # Release driver resources even if the test fails
        if driver is not None:
            driver.close()
            print("Database driver closed.")


if __name__ == "__main__":
    test_connection()

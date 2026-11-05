
"""
Neo4j connection manager for CloudNexus.

Responsibilities:
1. Read Neo4j credentials from environment variables.
2. Create a reusable Neo4j driver.
3. Verify database connectivity.
4. Provide database sessions.
5. Close the driver cleanly.

This module manages connections only.
It does not create graph nodes or write application data.
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


# Load environment variables from the extraction-service .env file.
load_dotenv()


class Neo4jClient:
    """Manages the connection between CloudNexus and Neo4j AuraDB."""

    def __init__(self):
        # Read configuration without hardcoding credentials.
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        # Fail early if required configuration is missing.
        missing = [
            name
            for name, value in {
                "NEO4J_URI": self.uri,
                "NEO4J_USERNAME": self.username,
                "NEO4J_PASSWORD": self.password,
            }.items()
            if not value
        ]

        if missing:
            raise ValueError(
                f"Missing Neo4j environment variables: {', '.join(missing)}"
            )

        # Create the driver. The driver manages the connection pool.
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )

    def verify_connection(self):
        """Check that Neo4j is reachable and credentials are valid."""
        self.driver.verify_connectivity()
        return True

    def execute_read(self, query, parameters=None):
        """Execute a read-only Cypher transaction."""
        with self.driver.session(database=self.database) as session:
            return session.execute_read(
                lambda tx: list(
                    tx.run(query, parameters or {}).data()
                )
            )

    def execute_write(self, query, parameters=None):
        """Execute a write Cypher transaction."""
        with self.driver.session(database=self.database) as session:
            return session.execute_write(
                lambda tx: list(
                    tx.run(query, parameters or {}).data()
                )
            )

    def close(self):
        """Release the driver's connection pool."""
        self.driver.close()

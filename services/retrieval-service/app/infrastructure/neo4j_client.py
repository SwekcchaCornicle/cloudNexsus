"""Shared Neo4j driver wrapper. Retrieval performs read operations only."""
from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, username, password, database):
        if not all((uri, username, password)):
            raise ValueError("Neo4j URI, username and password are required.")
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def verify_connectivity(self):
        """Check network/authentication during application startup."""
        self.driver.verify_connectivity()

    def execute_read(self, query: str, parameters: dict | None = None):
        """Execute parameterized Cypher against the configured database."""
        records, _, _ = self.driver.execute_query(
            query, parameters_=parameters or {}, database_=self.database, routing_="r"
        )
        return records

    def close(self):
        """Release the driver at application shutdown."""
        self.driver.close()

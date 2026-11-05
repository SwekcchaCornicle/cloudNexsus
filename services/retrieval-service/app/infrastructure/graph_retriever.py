
"""Retrieves knowledge graph relationships associated with a chunk.

The Extraction Service stores source_chunk_id on every RELATED_TO edge.
We use that exact property to retrieve the relationships generated from
the selected documentation chunk.
"""

class Neo4jGraphRetriever:

    def __init__(self, neo4j_client):
        self.neo4j = neo4j_client

    def relationships_for_chunk(self, chunk_id):
        """Find relationships extracted from this exact chunk."""

        query = """
        MATCH (source:Entity)-[rel:RELATED_TO]->(target:Entity)

        WHERE rel.source_chunk_id = $chunk_id

        RETURN
            source.name AS source,
            rel.predicate AS predicate,
            target.name AS target,
            rel.evidence AS evidence,
            rel.confidence AS confidence

        ORDER BY rel.confidence DESC
        """

        records = self.neo4j.execute_read(
            query,
            {"chunk_id": chunk_id}
        )

        return [record.data() for record in records]

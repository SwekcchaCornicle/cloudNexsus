"""Neo4j vector-index adapter. Assumes Chunk.embedding and a 1024-D index."""
class Neo4jVectorRetriever:
    def __init__(self, neo4j_client, index_name):
        self.neo4j, self.index_name = neo4j_client, index_name

    def search(self, query_embedding, top_k, provider=None, service_name=None):
        """Return semantically similar chunks and entities mentioned by each chunk."""
        # Index names cannot be parameterized in Cypher, so validate before interpolation.
        if not self.index_name.replace("_", "").isalnum():
            raise ValueError("Unsafe VECTOR_INDEX_NAME.")
        query = f"""
                    CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
                    YIELD node AS chunk, score
                    WHERE ($provider IS NULL OR toUpper(chunk.provider) = $provider)
                    AND ($service_name IS NULL OR toLower(chunk.service_name) = toLower($service_name))
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
        records = self.neo4j.execute_read(query, {
            "index_name": self.index_name, "top_k": top_k,
            "query_embedding": query_embedding,
            "provider": provider.upper() if provider else None,
            "service_name": service_name,
        })
        return [record.data() for record in records]

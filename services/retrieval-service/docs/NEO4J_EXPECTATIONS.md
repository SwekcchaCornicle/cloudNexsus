# Neo4j contract checklist

Expected graph:
`(Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)`
`(Entity)-[:RELATED_TO]->(Entity)`

Expected vector index: `chunk_embedding_index`, label `Chunk`, property `embedding`, 1,024 dimensions, cosine similarity, state ONLINE.

Run in Neo4j Browser:
```cypher
SHOW VECTOR INDEXES;
MATCH (c:Chunk) RETURN count(c) AS chunks, count(c.embedding) AS embedded_chunks;
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity) RETURN c, e LIMIT 10;
```

If labels/property names in the actual extraction repository differ, adjust the retrieval Cypher. Do not create a duplicate graph schema.

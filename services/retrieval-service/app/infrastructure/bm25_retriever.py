"""
BM25 keyword retrieval using Neo4j full-text search.

Neo4j's Lucene-backed full-text index ranks matching documentation chunks
by keyword relevance; its score is not a cosine similarity score.
"""
import re


class Neo4jBM25Retriever:
    def __init__(self, neo4j_client, index_name="chunk_content_fulltext"):
        self.neo4j = neo4j_client
        self.index_name = index_name

        if not re.fullmatch(r"[A-Za-z0-9_]+", index_name):
            raise ValueError("Invalid full-text index name.")

    @staticmethod
    def _build_lucene_query(question: str) -> str:
        terms = re.findall(r"[A-Za-z0-9_:./\\-]+", question)
        special_chars = r'+-&|!(){}[]^"~*?:\\/'
        escaped_terms = [
            "".join("\\" + char if char in special_chars else char for char in term)
            for term in terms
        ]
        return " OR ".join(escaped_terms)

    def search(
        self,
        question: str,
        top_k: int = 10,
        provider: str | None = None,
        service_name: str | None = None,
    ):
        """Search indexed Chunk.content using Neo4j full-text search."""
        if not question or not question.strip():
            raise ValueError("Search question cannot be empty.")
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        lucene_query = self._build_lucene_query(question)
        if not lucene_query:
            return []

        query = f"""
        CALL db.index.fulltext.queryNodes(
            '{self.index_name}',
            $lucene_query
        )
        YIELD node AS chunk, score
        WHERE ($provider IS NULL
               OR toUpper(chunk.provider) = $provider)
          AND ($service_name IS NULL
               OR toLower(chunk.service_name) = toLower($service_name))
        RETURN
            chunk.chunk_id AS chunk_id,
            chunk.content AS content,
            score AS score,
            chunk.provider AS provider,
            chunk.service_name AS service_name,
            chunk.source_url AS source_url,
            chunk.document_id AS document_id,
            chunk.embedding_model_id AS embedding_model
        ORDER BY score DESC
        LIMIT $top_k
        """

        records = self.neo4j.execute_read(
            query,
            {
                "lucene_query": lucene_query,
                "provider": provider.upper() if provider else None,
                "service_name": service_name,
                "top_k": top_k,
            },
        )
        return [record.data() for record in records]

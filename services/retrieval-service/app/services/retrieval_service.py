from app.domain.schemas import (
    RetrievalResponse,
    RetrievalResult,
    RetrievedEntity,
    RetrievedRelationship,
)
from app.services.rrf_ranker import ReciprocalRankFusion


class RetrievalService:

    def __init__(
        self,
        embedding_client,
        vector_retriever,
        bm25_retriever,
        graph_retriever,
    ):
        self.embedding_client = embedding_client
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.graph_retriever = graph_retriever

        self.rrf_ranker = ReciprocalRankFusion(k=60)

    def retrieve(self, request):
        """Run hybrid retrieval, fuse results, and enrich with graph data."""

        # 1. Convert the question into an embedding.
        query_embedding = self.embedding_client.embed_query(
            request.question
        )

        # 2. Semantic retrieval.
        vector_results = self.vector_retriever.search(
            query_embedding,
            request.top_k,
            request.provider,
            request.service_name,
        )

        for row in vector_results:
            row["retrieval_source"] = "vector"

        # 3. Keyword retrieval.
        bm25_results = self.bm25_retriever.search(
            question=request.question,
            top_k=request.top_k,
            provider=request.provider,
            service_name=request.service_name,
        )

        for row in bm25_results:
            row["retrieval_source"] = "bm25"

        # 4. Combine semantic and keyword results using RRF.
        ranked = self.rrf_ranker.fuse(
            result_lists=[
                vector_results,
                bm25_results,
            ],
            top_k=request.top_k,
        )

        # 5. Enrich the fused results with graph relationships.
        for row in ranked:
            row["relationships"] = (
                self.graph_retriever.relationships_for_chunk(
                    row["chunk_id"]
                )
            )

        # 6. Convert Neo4j dictionaries into validated API schemas.
        results = []

        for row in ranked:

            entities = [
                RetrievedEntity(**entity)
                for entity in row.get("entities", [])
                if entity and entity.get("name")
            ]

            relationships = [
                RetrievedRelationship(**relationship)
                for relationship in row.get("relationships", [])
                if (
                    relationship
                    and relationship.get("source")
                    and relationship.get("target")
                )
            ]

            results.append(
                RetrievalResult(
                    chunk_id=str(row["chunk_id"]),
                    content=row.get("content") or "",

                    # RRF ranking
                    score=float(row.get("rrf_score", 0.0)),
                    rrf_score=float(row.get("rrf_score", 0.0)),
                    retrieval_sources=row.get("retrieval_sources", []),

                    provider=row.get("provider"),
                    service_name=row.get("service_name"),
                    source_url=row.get("source_url"),
                    document_id=row.get("document_id"),
                    embedding_model=row.get("embedding_model"),

                    entities=entities,
                    relationships=relationships,
                )
            )

        return RetrievalResponse(
            question=request.question,
            provider_filter=request.provider,
            result_count=len(results),
            results=results,
        )
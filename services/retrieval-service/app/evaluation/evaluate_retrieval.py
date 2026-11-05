"""
Compare Vector Search, BM25 and Hybrid RRF retrieval.

Runs against the actual Neo4j database and Vertex AI embeddings.
"""

from statistics import mean

from app.config import get_settings

from app.infrastructure.embedding_client import VertexEmbeddingClient
from app.infrastructure.neo4j_client import Neo4jClient
from app.infrastructure.vector_retriever import Neo4jVectorRetriever
from app.infrastructure.bm25_retriever import Neo4jBM25Retriever

from app.services.rrf_ranker import ReciprocalRankFusion

from app.evaluation.dataset import EVALUATION_DATASET
from app.evaluation.metrics import evaluate_query


TOP_K = 2


def evaluate_method(method_name, retrieved_ids, relevant_ids):
    """Calculate metrics for one retrieval method."""

    return evaluate_query(
        retrieved_ids=retrieved_ids,
        relevant_ids=relevant_ids,
        k=TOP_K,
    )


def print_report(report):
    """Print average evaluation results."""

    print("\n" + "=" * 75)
    print("CLOUDNEXUS RETRIEVAL EVALUATION REPORT")
    print("=" * 75)

    print(
        f"{'Method':<15}"
        f"{'Precision@2':<15}"
        f"{'Recall@2':<15}"
        f"{'MRR':<15}"
        f"{'NDCG@2':<15}"
    )

    print("-" * 75)

    for method, metrics in report.items():

        print(
            f"{method:<15}"
            f"{metrics['precision@2']:<15.4f}"
            f"{metrics['recall@2']:<15.4f}"
            f"{metrics['mrr']:<15.4f}"
            f"{metrics['ndcg@2']:<15.4f}"
        )

    print("=" * 75)


def run_evaluation():

    settings = get_settings()
    settings.validate_runtime()

    embedding_client = VertexEmbeddingClient(
        settings.gcp_project_id,
        settings.gcp_region,
        settings.vertex_embedding_model,
        settings.embedding_dimensions,
    )

    neo4j = Neo4jClient(
        settings.neo4j_uri,
        settings.neo4j_username,
        settings.neo4j_password,
        settings.neo4j_database,
    )

    try:
        neo4j.verify_connectivity()

        vector_retriever = Neo4jVectorRetriever(
            neo4j,
            settings.vector_index_name,
        )

        bm25_retriever = Neo4jBM25Retriever(
            neo4j,
            index_name="chunk_content_fulltext",
        )

        rrf_ranker = ReciprocalRankFusion(k=60)

        report = {
            "Vector": [],
            "BM25": [],
            "Hybrid RRF": [],
        }

        for test_case in EVALUATION_DATASET:

            question = test_case["question"]
            provider = test_case.get("provider")
            service_name = test_case.get("service_name")
            relevant_ids = test_case["relevant_chunk_ids"]

            print("\nQuestion:", question)

            # 1. Generate query embedding.
            query_embedding = embedding_client.embed_query(question)

            # 2. Vector retrieval.
            vector_results = vector_retriever.search(
                query_embedding,
                TOP_K,
                provider,
                service_name,
            )

            # 3. BM25 retrieval.
            bm25_results = bm25_retriever.search(
                question=question,
                top_k=TOP_K,
                provider=provider,
                service_name=service_name,
            )

            # 4. Hybrid retrieval.
            hybrid_results = rrf_ranker.fuse(
                result_lists=[
                    vector_results,
                    bm25_results,
                ],
                top_k=TOP_K,
            )

            # 5. Extract returned chunk IDs.
            vector_ids = [
                row["chunk_id"] for row in vector_results
            ]

            bm25_ids = [
                row["chunk_id"] for row in bm25_results
            ]

            hybrid_ids = [
                row["chunk_id"] for row in hybrid_results
            ]

            # 6. Calculate metrics for each method.
            report["Vector"].append(
                evaluate_method(
                    "Vector",
                    vector_ids,
                    relevant_ids,
                )
            )

            report["BM25"].append(
                evaluate_method(
                    "BM25",
                    bm25_ids,
                    relevant_ids,
                )
            )

            report["Hybrid RRF"].append(
                evaluate_method(
                    "Hybrid RRF",
                    hybrid_ids,
                    relevant_ids,
                )
            )

            print("Expected:", relevant_ids)
            print("Vector:", vector_ids)
            print("BM25:", bm25_ids)
            print("Hybrid:", hybrid_ids)

        # 7. Calculate average metrics across test questions.
        average_report = {}

        for method, query_metrics in report.items():

            average_report[method] = {
                metric: mean(
                    result[metric] for result in query_metrics
                )
                for metric in query_metrics[0]
            }

        print_report(average_report)

    finally:
        neo4j.close()


if __name__ == "__main__":
    run_evaluation()
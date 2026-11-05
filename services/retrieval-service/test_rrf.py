from app.services.rrf_ranker import ReciprocalRankFusion


vector_results = [
    {
        "chunk_id": "chunk-A",
        "content": "Event source mapping invokes Lambda.",
        "retrieval_source": "vector",
    },
    {
        "chunk_id": "chunk-B",
        "content": "Lambda is a serverless compute service.",
        "retrieval_source": "vector",
    },
]

bm25_results = [
    {
        "chunk_id": "chunk-B",
        "content": "Lambda is a serverless compute service.",
        "retrieval_source": "bm25",
    },
    {
        "chunk_id": "chunk-A",
        "content": "Event source mapping invokes Lambda.",
        "retrieval_source": "bm25",
    },
]

ranker = ReciprocalRankFusion(k=60)

results = ranker.fuse(
    result_lists=[vector_results, bm25_results],
    top_k=5,
)

print("\nRRF Results")
print("=" * 50)

for result in results:
    print("Chunk ID:", result["chunk_id"])
    print("RRF Score:", round(result["rrf_score"], 6))
    print("Sources:", result["retrieval_sources"])
    print("-" * 50)
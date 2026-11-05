from typing import Any


class ReciprocalRankFusion:
    """Combine ranked retrieval results using Reciprocal Rank Fusion."""

    def __init__(self, k: int = 60):
        if k <= 0:
            raise ValueError("k must be greater than zero")

        self.k = k

    def fuse(
        self,
        result_lists: list[list[dict[str, Any]]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        fused = {}

        for results in result_lists:
            for rank, result in enumerate(results, start=1):

                chunk_id = result.get("chunk_id")

                if not chunk_id:
                    continue

                if chunk_id not in fused:
                    fused[chunk_id] = {
                        **result,
                        "rrf_score": 0.0,
                        "retrieval_sources": [],
                    }

                fused[chunk_id]["rrf_score"] += 1 / (self.k + rank)

                source = result.get("retrieval_source")

                if (
                    source
                    and source not in fused[chunk_id]["retrieval_sources"]
                ):
                    fused[chunk_id]["retrieval_sources"].append(source)

        return sorted(
            fused.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )[:top_k]
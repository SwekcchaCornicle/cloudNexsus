"""
Retrieval evaluation metrics.

Implements:
- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain (NDCG@K)
"""


import math


def precision_at_k(retrieved_ids, relevant_ids, k=5):
    """Calculate the fraction of top-K results that are relevant."""

    if k < 1:
        raise ValueError("k must be at least 1")

    retrieved = retrieved_ids[:k]

    if not retrieved:
        return 0.0

    relevant = set(relevant_ids)

    hits = sum(
        1 for chunk_id in retrieved
        if chunk_id in relevant
    )

    return hits / k


def recall_at_k(retrieved_ids, relevant_ids, k=5):
    """Calculate the fraction of relevant chunks found in top-K."""

    relevant = set(relevant_ids)

    if not relevant:
        return 0.0

    retrieved = retrieved_ids[:k]

    hits = sum(
        1 for chunk_id in retrieved
        if chunk_id in relevant
    )

    return hits / len(relevant)


def reciprocal_rank(retrieved_ids, relevant_ids):
    """Return the reciprocal rank of the first relevant result."""

    relevant = set(relevant_ids)

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant:
            return 1 / rank

    return 0.0


def ndcg_at_k(retrieved_ids, relevant_ids, k=5):
    """Calculate NDCG@K using binary relevance labels."""

    if k < 1:
        raise ValueError("k must be at least 1")

    relevant = set(relevant_ids)

    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, chunk_id in enumerate(retrieved_ids[:k], start=1)
        if chunk_id in relevant
    )

    ideal_relevant_count = min(len(relevant), k)

    ideal_dcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    if ideal_dcg == 0:
        return 0.0

    return dcg / ideal_dcg


def evaluate_query(retrieved_ids, relevant_ids, k=5):
    """Calculate all retrieval metrics for one query."""

    return {
        f"precision@{k}": precision_at_k(
            retrieved_ids, relevant_ids, k
        ),
        f"recall@{k}": recall_at_k(
            retrieved_ids, relevant_ids, k
        ),
        "mrr": reciprocal_rank(
            retrieved_ids, relevant_ids
        ),
        f"ndcg@{k}": ndcg_at_k(
            retrieved_ids, relevant_ids, k
        ),
    }
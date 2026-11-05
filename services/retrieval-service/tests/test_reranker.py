from app.services.reranker import lexical_overlap, rerank_results

def test_lexical_overlap_detects_terms():
    assert lexical_overlap("AWS Lambda S3", "AWS Lambda can read S3 objects") > 0

def test_reranker_returns_sorted_rows():
    rows = [{"score": 0.9, "content": "unrelated"}, {"score": 0.8, "content": "AWS Lambda S3"}]
    ranked = rerank_results("AWS Lambda S3", rows)
    assert ranked[0]["rerank_score"] >= ranked[1]["rerank_score"]

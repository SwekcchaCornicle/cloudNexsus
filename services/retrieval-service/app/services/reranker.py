"""Simple explainable baseline reranker, not a trained cross-encoder."""
import re

def lexical_overlap(question, content):
    """Measure how many meaningful question tokens also occur in the chunk."""
    terms = {t.lower() for t in re.findall(r"[A-Za-z0-9_]+", question) if len(t) > 2}
    words = set(re.findall(r"[A-Za-z0-9_]+", content.lower()))
    return len(terms & words) / len(terms) if terms else 0.0

def rerank_results(question, results):
    """Blend Neo4j vector similarity with exact-term overlap (85% / 15%)."""
    for row in results:
        semantic = float(row.get("score") or 0.0)
        lexical = lexical_overlap(question, row.get("content") or "")
        row["rerank_score"] = 0.85 * semantic + 0.15 * lexical
    return sorted(results, key=lambda row: row["rerank_score"], reverse=True)

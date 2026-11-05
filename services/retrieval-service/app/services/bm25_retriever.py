
"""Backward-compatible import for the BM25 infrastructure adapter."""
from app.infrastructure.bm25_retriever import Neo4jBM25Retriever

__all__ = ["Neo4jBM25Retriever"]

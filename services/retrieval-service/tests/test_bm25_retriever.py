from unittest.mock import Mock

import pytest
from app.infrastructure.bm25_retriever import Neo4jBM25Retriever


def test_search_passes_query_and_filters_to_neo4j():
    result = {"chunk_id": "chunk-1", "score": 1.2}
    client = Mock()
    client.execute_read.return_value = [Mock(data=Mock(return_value=result))]
    retriever = Neo4jBM25Retriever(client)

    assert retriever.search(
        "event source mapping Lambda",
        top_k=5,
        provider="AWS",
        service_name="Lambda",
    ) == [result]

    query, parameters = client.execute_read.call_args.args
    assert "db.index.fulltext.queryNodes" in query
    assert parameters == {
        "lucene_query": "event OR source OR mapping OR Lambda",
        "provider": "AWS",
        "service_name": "Lambda",
        "top_k": 5,
    }


def test_search_rejects_empty_question():
    retriever = Neo4jBM25Retriever(Mock())

    with pytest.raises(ValueError, match="cannot be empty"):
        retriever.search("  ")

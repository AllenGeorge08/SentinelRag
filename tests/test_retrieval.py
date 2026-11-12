"""Retrieval phase tests — real hybrid retrieval (dense + BM25 + RRF) and LLM generation (no mocks)."""

import pytest

from app.rag.queues.worker import process_query


@pytest.mark.parametrize("query", [
    "What is prompt injection?",
    "What is retrieval poisoning in a RAG system?",
    "What are the four core NIST AI risk management functions?",
])
def test_process_query_returns_grounded_answer(query):
    result = process_query(query)

    assert "answer" in result
    assert "documents" in result

    answer = result["answer"]
    assert isinstance(answer, str)
    assert len(answer.strip()) > 0, "Generated answer is empty"

    documents = result["documents"]
    assert documents is not None
    assert hasattr(documents, "points")
    assert len(documents.points) > 0, "No documents retrieved"

    # Each retrieved point should carry page + source metadata for citations
    for point in documents.points:
        assert point.payload is not None
        assert "text" in point.payload
        assert "page" in point.payload
        assert "source" in point.payload

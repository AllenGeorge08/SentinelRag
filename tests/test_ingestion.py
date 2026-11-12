"""Ingestion phase tests — real PDF loading, chunking, and Qdrant indexing (no mocks)."""

import pytest
from pathlib import Path

from app.rag.ingestion.index import (
    load_docs, parse_pdf, chunk_pdf, chunk_all_pdfs, build_points,
    pdf_dir, COLLECTION_NAME,
)
from app.rag.clients.qdrant_client import client
from qdrant_client.models import PointStruct


def test_load_docs_returns_documents_from_pdfs():
    docs = load_docs(pdf_dir)
    assert len(docs) > 0, "No documents loaded from PDFs"
    non_empty = [d for d in docs if d.page_content.strip()]
    assert len(non_empty) > 0, "No documents with extractable text"
    for doc in docs:
        assert hasattr(doc, "page_content")
        assert "source" in doc.metadata


def test_parse_pdf_returns_pages_with_text():
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    assert len(pdfs) > 0, "No PDFs found in app/data"
    pages = parse_pdf(pdfs[0])
    assert len(pages) > 0, f"No pages parsed from {pdfs[0].name}"
    for page in pages:
        assert "page" in page
        assert "text" in page
        assert len(page["text"].strip()) > 0


def test_chunk_pdf_yields_chunks_with_metadata():
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    pages = parse_pdf(pdfs[0])
    chunks = list(chunk_pdf(pages, source=pdfs[0].name))
    assert len(chunks) > 0, f"No chunks produced from {pdfs[0].name}"
    for chunk in chunks:
        assert "text" in chunk and len(chunk["text"]) > 0
        assert "page" in chunk
        assert "chunk_id" in chunk
        assert "source" in chunk


def test_chunk_all_pdfs_produces_chunks():
    chunks = list(chunk_all_pdfs(pdf_dir))
    assert len(chunks) > 0, "No chunks produced across all PDFs"


def test_build_points_yields_point_structs():
    chunks = list(chunk_all_pdfs(pdf_dir))
    points = list(build_points(
        chunks,
        dense_model="sentence-transformers/all-MiniLM-l6-v2",
        sparse_model="qdrant/bm25",
        late_model="answerdotai/answerai-colbert-small-v1",
    ))
    assert len(points) > 0, "No points built from chunks"
    for point in points:
        assert isinstance(point, PointStruct)
        assert "dense" in point.vector
        assert "sparse" in point.vector
        assert "multi" in point.vector
        assert "text" in point.payload


def test_qdrant_collection_exists_and_has_points():
    assert client.collection_exists(COLLECTION_NAME), "Qdrant collection not found"
    info = client.get_collection(COLLECTION_NAME)
    assert info.points_count > 0, "Qdrant collection has no indexed points"

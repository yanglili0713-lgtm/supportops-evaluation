from __future__ import annotations

from pathlib import Path

import pytest

from rag.chunker import chunk_documents
from rag.dense_retriever import DenseEmbeddingRetriever
from rag.ingest import Document
from rag.faiss_index import FaissHNSWIndex, is_faiss_available


def test_dense_embedding_retriever_works_without_external_model():
    docs = [
        Document(
            doc_id="rag_upload_troubleshooting",
            source="rag_upload_troubleshooting.md",
            text="上传 PDF 后检索不到内容，可能是向量写入失败或 OCR 问题。",
        ),
        Document(
            doc_id="refund_policy",
            source="refund_policy.md",
            text="退款需要检查支付状态和 invoice。",
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=120, chunk_overlap=10)
    retriever = DenseEmbeddingRetriever(chunks, allow_fallback=True)

    results = retriever.search("文档导入后答案没有依据", top_k=1)

    assert results
    assert results[0].doc_id == "rag_upload_troubleshooting"
    assert results[0].dense_score is not None


def test_dense_embedding_retriever_save_and_load_round_trip(tmp_path):
    docs = [
        Document(
            doc_id="api_key_guide",
            source="api_key_guide.md",
            text="API Key 失效可能与权限或套餐有关。",
        )
    ]
    chunks = chunk_documents(docs, chunk_size=120, chunk_overlap=10)
    retriever = DenseEmbeddingRetriever(chunks, allow_fallback=True)

    path = retriever.save(tmp_path / "dense_index")
    loaded = DenseEmbeddingRetriever.load(path)
    results = loaded.search("API Key 失效", top_k=1)

    assert results
    assert results[0].doc_id == "api_key_guide"


@pytest.mark.skipif(not is_faiss_available(), reason="faiss is not installed")
def test_faiss_hnsw_index_round_trip(tmp_path):
    docs = [
        Document(doc_id="doc_a", source="a.md", text="alpha beta gamma"),
        Document(doc_id="doc_b", source="b.md", text="delta epsilon zeta"),
    ]
    chunks = chunk_documents(docs, chunk_size=120, chunk_overlap=10)
    vectors = [[1.0, 0.0], [0.0, 1.0]]

    index = FaissHNSWIndex.build_index(vectors, chunks)
    path = index.save(tmp_path / "faiss")
    loaded = FaissHNSWIndex.load(path)
    results = loaded.search([1.0, 0.0], top_k=1)

    assert results
    assert results[0]["chunk"].doc_id == "doc_a"

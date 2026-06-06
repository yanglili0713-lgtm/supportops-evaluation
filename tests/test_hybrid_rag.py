from rag.chunker import chunk_documents
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import Document, load_markdown_docs
from rag.reranker import rerank_results
from rag.retriever import RetrievalResult
from rag.vector_store import SimpleVectorStore


def _hybrid() -> HybridRetriever:
    docs = load_markdown_docs("data/docs")
    return HybridRetriever(chunk_documents(docs), alpha=0.6)


def test_hybrid_retrieves_rag_upload_troubleshooting_for_no_space_pdf_query():
    results = _hybrid().search("上传PDF后检索不到内容怎么办？", top_k=3)

    assert any(result.doc_id == "rag_upload_troubleshooting" for result in results)


def test_hybrid_retrieves_api_key_guide():
    results = _hybrid().search("API Key 失效怎么办？", top_k=3)

    assert any(result.doc_id == "api_key_guide" for result in results)


def test_hybrid_returns_citations():
    results = _hybrid().search("上传 PDF 后检索不到内容", top_k=3)

    assert results
    assert all(result.doc_id and result.chunk_id and result.source for result in results)


def test_reranker_keeps_source_and_chunk_id():
    original = RetrievalResult(
        chunk_id="doc:0",
        doc_id="doc",
        source="doc.md",
        text="上传 PDF 后检索不到内容",
        score=0.5,
    )

    reranked = rerank_results("上传 PDF", [original], top_k=1)

    assert reranked[0].source == "doc.md"
    assert reranked[0].chunk_id == "doc:0"


def test_vector_search_handles_near_semantic_query():
    docs = [
        Document(
            doc_id="rag_upload_troubleshooting",
            source="rag_upload_troubleshooting.md",
            text="上传 PDF 后检索不到内容，可能是向量库没有写入或 embedding 任务失败。",
        ),
        Document(
            doc_id="refund_policy",
            source="refund_policy.md",
            text="用户购买后可以申请退款。",
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=120, chunk_overlap=10)
    store = SimpleVectorStore()
    store.add_chunks(chunks)

    results = store.search("文档导入后答案没有依据", top_k=1)

    assert results
    assert results[0].doc_id == "rag_upload_troubleshooting"

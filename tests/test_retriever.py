from rag.chunker import chunk_documents
from rag.ingest import Document
from rag.retriever import BM25Retriever


def test_bm25_retrieves_refund_policy():
    docs = [
        Document(
            doc_id="refund_policy",
            source="refund_policy.md",
            text="用户在购买后 7 天内可以申请退款，必须先查询 invoice。",
        ),
        Document(
            doc_id="api_key_guide",
            source="api_key_guide.md",
            text="API Key 失效可能是套餐过期或权限不足。",
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=10)
    retriever = BM25Retriever(chunks)

    results = retriever.search("用户想申请退款，需要查询 invoice 吗", top_k=1)

    assert results
    assert results[0].doc_id == "refund_policy"


def test_bm25_retrieves_api_key_guide():
    docs = [
        Document(
            doc_id="refund_policy",
            source="refund_policy.md",
            text="退款需要检查订单状态。",
        ),
        Document(
            doc_id="api_key_guide",
            source="api_key_guide.md",
            text="API Key 失效常见原因包括 key 被删除、套餐过期、权限不足。",
        ),
    ]
    chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=10)
    retriever = BM25Retriever(chunks)

    results = retriever.search("API Key 失效 权限不足", top_k=1)

    assert results
    assert results[0].doc_id == "api_key_guide"

from __future__ import annotations

from rag.chunker import chunk_documents
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import load_markdown_docs


def run_eval(
    force_fallback_embedding: bool | None = None,
    offline: bool | None = None,
    mock_backend: bool | None = None,
) -> dict:
    docs = load_markdown_docs("data/docs")
    chunks = chunk_documents(docs)
    retriever = HybridRetriever(
        chunks,
        alpha=0.6,
        force_fallback=force_fallback_embedding,
        offline=offline,
        mock_backend=mock_backend,
    )
    cases = [
        ("上传PDF后检索不到内容怎么办？", "rag_upload_troubleshooting"),
        ("API Key 失效怎么办？", "api_key_guide"),
        ("文档导入后答案没有依据", "rag_upload_troubleshooting"),
    ]

    checks = {}
    details = []
    for query, expected_doc in cases:
        results = retriever.search(query, top_k=3)
        found = any(expected_doc in result.doc_id for result in results)
        has_citation = all(result.doc_id and result.chunk_id and result.source for result in results)
        key = expected_doc + ":" + query
        checks[f"{key}:found_expected_doc"] = found
        checks[f"{key}:has_citation"] = bool(results) and has_citation
        details.append(
            {
                "query": query,
                "expected_doc": expected_doc,
                "citations": [
                    {
                        "doc_id": result.doc_id,
                        "chunk_id": result.chunk_id,
                        "source": result.source,
                        "score": round(result.score, 4),
                    }
                    for result in results
                ],
            }
        )

    failed_checks = [name for name, passed in checks.items() if not passed]
    return {
        "name": "hybrid_rag_eval",
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": details,
    }


if __name__ == "__main__":
    print(run_eval())

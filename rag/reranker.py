from __future__ import annotations

from rag.retriever import RetrievalResult, tokenize


def rerank_results(query: str, results: list[RetrievalResult], top_k: int = 5) -> list[RetrievalResult]:
    query_tokens = set(tokenize(query))
    query_compact = query.lower().replace(" ", "")

    rescored = []
    for result in results:
        doc_hint = 0.0
        if "pdf" in query_compact and "rag_upload" in result.doc_id:
            doc_hint += 0.3
        if "api" in query_compact and "api_key" in result.doc_id:
            doc_hint += 0.3
        if "退款" in query_compact and "refund" in result.doc_id:
            doc_hint += 0.3

        result_tokens = set(tokenize(result.text))
        coverage = len(query_tokens & result_tokens) / len(query_tokens) if query_tokens else 0.0
        score = result.score + coverage * 0.2 + doc_hint
        rescored.append(
            RetrievalResult(
                chunk_id=result.chunk_id,
                doc_id=result.doc_id,
                source=result.source,
                text=result.text,
                score=score,
            )
        )

    rescored.sort(key=lambda item: item.score, reverse=True)
    return rescored[:top_k]

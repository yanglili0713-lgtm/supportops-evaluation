from __future__ import annotations

from rag.chunker import Chunk
from rag.reranker import rerank_results
from rag.retriever import BM25Retriever, RetrievalResult
from rag.vector_store import SimpleVectorStore


class HybridRetriever:
    def __init__(self, chunks: list[Chunk], alpha: float = 0.6) -> None:
        if alpha < 0 or alpha > 1:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.bm25 = BM25Retriever(chunks)
        self.vector_store = SimpleVectorStore()
        self.vector_store.add_chunks(chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        vector_results = self.vector_store.search(query, top_k=top_k * 2)
        merged = self._merge_results(bm25_results, vector_results)
        return rerank_results(query, merged, top_k=top_k)

    def _merge_results(
        self,
        bm25_results: list[RetrievalResult],
        vector_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        bm25_scores = _normalize_scores(bm25_results)
        vector_scores = _normalize_scores(vector_results)
        by_chunk = {result.chunk_id: result for result in bm25_results + vector_results}

        merged = []
        for chunk_id, result in by_chunk.items():
            score = self.alpha * bm25_scores.get(chunk_id, 0.0)
            score += (1 - self.alpha) * vector_scores.get(chunk_id, 0.0)
            merged.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    source=result.source,
                    text=result.text,
                    score=score,
                )
            )
        merged.sort(key=lambda item: item.score, reverse=True)
        return merged


def _normalize_scores(results: list[RetrievalResult]) -> dict[str, float]:
    if not results:
        return {}
    max_score = max(result.score for result in results) or 1.0
    return {result.chunk_id: result.score / max_score for result in results}

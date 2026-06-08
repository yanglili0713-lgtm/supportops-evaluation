from __future__ import annotations

from dataclasses import replace

from rag.chunker import Chunk
from rag.dense_retriever import DenseEmbeddingRetriever
from rag.reranker import describe_reranker_backend, rerank_results
from rag.retriever import BM25Retriever, RetrievalResult


class HybridRetriever:
    """Linear score fusion retriever.

    alpha = 1.0 means the score is fully BM25-weighted.
    alpha = 0.0 means the score is fully dense-weighted.
    hybrid_score = alpha * bm25_score + (1 - alpha) * dense_score
    """

    def __init__(
        self,
        chunks: list[Chunk],
        alpha: float = 0.6,
        model_name: str | None = None,
        use_faiss: bool = True,
        allow_fallback: bool = True,
        force_fallback: bool | None = None,
        offline: bool | None = None,
        mock_backend: bool | None = None,
        bm25: BM25Retriever | None = None,
        dense: DenseEmbeddingRetriever | None = None,
        reranker_model_name: str | None = None,
    ) -> None:
        if alpha < 0 or alpha > 1:
            raise ValueError("alpha must be between 0 and 1")
        self.alpha = alpha
        self.bm25 = bm25 or BM25Retriever(chunks)
        self.dense = dense or DenseEmbeddingRetriever(
            chunks,
            model_name=model_name,
            use_faiss=use_faiss,
            allow_fallback=allow_fallback,
            force_fallback=force_fallback,
            offline=offline,
            mock_backend=mock_backend,
        )
        self._reranker_backend = describe_reranker_backend(reranker_model_name)

    def search(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
        use_cross_encoder: bool = True,
    ) -> list[RetrievalResult]:
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        dense_results = self.dense.search(query, top_k=top_k * 2)
        merged = self._merge_results(bm25_results, dense_results)
        if rerank:
            return rerank_results(query, merged, top_k=top_k, use_cross_encoder=use_cross_encoder)
        merged.sort(key=lambda item: item.score, reverse=True)
        return merged[:top_k]

    def _merge_results(
        self,
        bm25_results: list[RetrievalResult],
        dense_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        bm25_scores = _normalize_scores(bm25_results)
        dense_scores = _normalize_scores(dense_results)
        by_chunk = {result.chunk_id: result for result in bm25_results + dense_results}

        merged = []
        for chunk_id, result in by_chunk.items():
            bm25_score = bm25_scores.get(chunk_id, 0.0)
            dense_score = dense_scores.get(chunk_id, 0.0)
            hybrid_score = self.alpha * bm25_score + (1 - self.alpha) * dense_score
            merged.append(
                replace(
                    result,
                    score=hybrid_score,
                    bm25_score=bm25_score,
                    dense_score=dense_score,
                    hybrid_score=hybrid_score,
                )
            )
        merged.sort(key=lambda item: item.score, reverse=True)
        return merged

    def backend_info(self) -> dict[str, object]:
        dense_backend = getattr(self.dense, "backend_name", "unknown")
        index_backend = getattr(self.dense, "index_backend", "unknown")
        fallback_used = bool(
            getattr(self.dense, "is_fallback_backend", False)
            or str(dense_backend).startswith("fallback")
            or str(index_backend).startswith("fallback")
        )
        return {
            "dense_backend": f"{dense_backend}:{index_backend}",
            "reranker_backend": self._reranker_backend.get("backend", "unknown"),
            "fallback_used": fallback_used,
        }


def _normalize_scores(results: list[RetrievalResult]) -> dict[str, float]:
    if not results:
        return {}
    max_score = max(result.score for result in results) or 1.0
    return {result.chunk_id: result.score / max_score for result in results}

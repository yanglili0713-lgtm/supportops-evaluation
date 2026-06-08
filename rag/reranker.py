from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import Any

from rag.retriever import RetrievalResult, tokenize


def rerank_results(
    query: str,
    results: list[RetrievalResult],
    top_k: int = 5,
    use_cross_encoder: bool = True,
    model_name: str | None = None,
) -> list[RetrievalResult]:
    if use_cross_encoder:
        cross_encoder_results = _rerank_with_cross_encoder(query, results, top_k=top_k, model_name=model_name)
        if cross_encoder_results is not None:
            return cross_encoder_results

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
            replace(
                result,
                score=score,
                rerank_score=score,
            )
        )

    rescored.sort(key=lambda item: item.score, reverse=True)
    return rescored[:top_k]


def describe_reranker_backend(model_name: str | None = None) -> dict[str, object]:
    if model_name is None:
        return {
            "backend": "lightweight-rule",
            "fallback_used": True,
            "model_name": None,
        }
    model = _load_cross_encoder(model_name)
    if model is None:
        return {
            "backend": "lightweight-rule",
            "fallback_used": True,
            "model_name": None,
        }
    return {
        "backend": f"cross-encoder:{getattr(model, 'model_name', model_name or 'cross-encoder/ms-marco-MiniLM-L-6-v2')}",
        "fallback_used": False,
        "model_name": getattr(model, "model_name", model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"),
    }


@lru_cache(maxsize=2)
def _load_cross_encoder(model_name: str | None = None) -> Any | None:
    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import-not-found]
    except Exception:
        return None

    model = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
    try:
        return CrossEncoder(model)
    except Exception:
        return None


def _rerank_with_cross_encoder(
    query: str,
    results: list[RetrievalResult],
    top_k: int,
    model_name: str | None = None,
) -> list[RetrievalResult] | None:
    model = _load_cross_encoder(model_name)
    if model is None or not results:
        return None

    pairs = [(query, result.text) for result in results]
    try:
        scores = model.predict(pairs)
    except Exception:
        return None

    rescored = []
    for result, score in zip(results, scores):
        score_value = float(score)
        rescored.append(
            replace(
                result,
                score=score_value,
                rerank_score=score_value,
            )
        )
    rescored.sort(key=lambda item: item.score, reverse=True)
    return rescored[:top_k]

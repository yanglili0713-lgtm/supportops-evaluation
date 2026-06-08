from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from rag.retriever import tokenize


DEFAULT_EMBEDDING_MODELS = (
    "BAAI/bge-small-en-v1.5",
    "all-MiniLM-L6-v2",
)


class EmbeddingBackend(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


@dataclass
class FallbackTokenEmbeddingBackend:
    name: str = "fallback-token-embedding"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vocab = _build_vocab(texts)
        return [_vectorize(text, vocab) for text in texts]


class SentenceTransformerEmbeddingBackend:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or _first_available_model()
        if not self.model_name:
            raise RuntimeError("No sentence-transformers model configured")

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("sentence-transformers is not installed") from exc

        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to load embedding model: {self.model_name}") from exc

        self.name = f"sentence-transformers:{self.model_name}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return _to_list_of_lists(vectors)


def load_embedding_backend(
    model_name: str | None = None,
    allow_fallback: bool = True,
    force_fallback: bool | None = None,
    offline: bool | None = None,
    mock_backend: bool | None = None,
) -> EmbeddingBackend:
    if _should_force_fallback(force_fallback=force_fallback, offline=offline, mock_backend=mock_backend):
        return FallbackTokenEmbeddingBackend()
    try:
        return SentenceTransformerEmbeddingBackend(model_name=model_name)
    except Exception:
        if allow_fallback:
            return FallbackTokenEmbeddingBackend()
        raise


def _first_available_model() -> str | None:
    return DEFAULT_EMBEDDING_MODELS[0] if DEFAULT_EMBEDDING_MODELS else None


def _should_force_fallback(
    force_fallback: bool | None = None,
    offline: bool | None = None,
    mock_backend: bool | None = None,
) -> bool:
    if force_fallback is not None:
        return force_fallback
    if offline is not None:
        return offline
    if mock_backend is not None:
        return mock_backend
    return any(
        _env_truthy(name)
        for name in (
            "SUPPORTOPS_FORCE_FALLBACK_EMBEDDING",
            "SUPPORTOPS_MOCK_EMBEDDING",
            "HF_HUB_OFFLINE",
            "TRANSFORMERS_OFFLINE",
        )
    )


def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "")
    return value.lower() in {"1", "true", "yes", "on"}


def _build_vocab(texts: list[str]) -> list[str]:
    vocab: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for token in tokenize(text):
            if token not in seen:
                seen.add(token)
                vocab.append(token)
    return vocab


def _vectorize(text: str, vocab: list[str]) -> list[float]:
    counts = Counter(tokenize(text))
    if not vocab:
        return []
    vector = [float(counts.get(token, 0)) for token in vocab]
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _to_list_of_lists(vectors: object) -> list[list[float]]:
    if hasattr(vectors, "tolist"):
        return [list(map(float, row)) for row in vectors.tolist()]
    return [list(map(float, row)) for row in vectors]  # type: ignore[arg-type]

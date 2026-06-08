from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rag.chunker import Chunk
from rag.embeddings import (
    FallbackTokenEmbeddingBackend,
    load_embedding_backend,
)
from rag.faiss_index import FaissHNSWIndex, is_faiss_available
from rag.retriever import RetrievalResult
from rag.vector_store import SimpleVectorStore


@dataclass
class DenseRetrieverConfig:
    model_name: str | None = None
    use_faiss: bool = True
    allow_fallback: bool = True


class DenseEmbeddingRetriever:
    def __init__(
        self,
        chunks: list[Chunk],
        model_name: str | None = None,
        use_faiss: bool = True,
        allow_fallback: bool = True,
        force_fallback: bool | None = None,
        offline: bool | None = None,
        mock_backend: bool | None = None,
    ) -> None:
        self.chunks = chunks
        self.config = DenseRetrieverConfig(
            model_name=model_name,
            use_faiss=use_faiss,
            allow_fallback=allow_fallback,
        )
        self.embedding_backend = load_embedding_backend(
            model_name=model_name,
            allow_fallback=allow_fallback,
            force_fallback=force_fallback,
            offline=offline,
            mock_backend=mock_backend,
        )
        self.backend_name = self.embedding_backend.name
        self.index_backend = "fallback"
        self._fallback_store: SimpleVectorStore | None = None
        self._faiss_index: FaissHNSWIndex | None = None
        self._vectors: list[list[float]] = []

        self._build_index()

    @property
    def is_fallback_backend(self) -> bool:
        return str(self.backend_name).startswith("fallback") or str(self.index_backend).startswith("fallback")

    def _build_index(self) -> None:
        texts = [chunk.text for chunk in self.chunks]
        if not texts:
            self._fallback_store = SimpleVectorStore()
            return

        if isinstance(self.embedding_backend, FallbackTokenEmbeddingBackend):
            self._fallback_store = SimpleVectorStore()
            self._fallback_store.add_chunks(self.chunks)
            self.index_backend = "fallback_token"
            return

        try:
            vectors = self.embedding_backend.embed(texts)
        except Exception:
            if not self.config.allow_fallback:
                raise
            self._fallback_store = SimpleVectorStore()
            self._fallback_store.add_chunks(self.chunks)
            self.backend_name = FallbackTokenEmbeddingBackend().name
            self.index_backend = "fallback_token"
            return

        self._vectors = vectors
        if self.config.use_faiss and is_faiss_available():
            try:
                self._faiss_index = FaissHNSWIndex.build_index(vectors, self.chunks)
                self.index_backend = "faiss_hnsw"
                return
            except Exception:
                if not self.config.allow_fallback:
                    raise

        self._fallback_store = SimpleVectorStore()
        self._fallback_store.add_chunks(self.chunks)
        self.index_backend = "fallback_token"

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not query or not self.chunks:
            return []

        if self._faiss_index is not None:
            query_vector = self.embedding_backend.embed([query])[0]
            results = self._faiss_index.search(query_vector, top_k=top_k)
            return [
                RetrievalResult(
                    chunk_id=item["chunk"].chunk_id,
                    doc_id=item["chunk"].doc_id,
                    source=item["chunk"].source,
                    text=item["chunk"].text,
                    score=float(item["score"]),
                    dense_score=float(item["score"]),
                )
                for item in results
            ]

        if self._fallback_store is None:
            return []

        results = self._fallback_store.search(query, top_k=top_k)
        converted: list[RetrievalResult] = []
        for result in results:
            converted.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    doc_id=result.doc_id,
                    source=result.source,
                    text=result.text,
                    score=result.score,
                    dense_score=result.score,
                )
            )
        return converted

    def save(self, path: str | Path) -> Path:
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        metadata = {
            "backend_name": self.backend_name,
            "index_backend": self.index_backend,
            "model_name": self.config.model_name,
            "use_faiss": self.config.use_faiss,
            "allow_fallback": self.config.allow_fallback,
            "chunks": [chunk.__dict__ for chunk in self.chunks],
        }
        (root / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        if self._faiss_index is not None:
            self._faiss_index.save(root / "faiss")
        return root

    def backend_info(self) -> dict[str, object]:
        return {
            "dense_backend": self.backend_name,
            "index_backend": self.index_backend,
            "fallback_used": self.is_fallback_backend,
        }

    @classmethod
    def load(cls, path: str | Path) -> "DenseEmbeddingRetriever":
        root = Path(path)
        metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        chunks = [Chunk(**chunk) for chunk in metadata["chunks"]]
        retriever = cls(
            chunks=chunks,
            model_name=metadata.get("model_name"),
            use_faiss=metadata.get("use_faiss", True),
            allow_fallback=metadata.get("allow_fallback", True),
        )
        faiss_dir = root / "faiss"
        if faiss_dir.exists() and is_faiss_available():
            retriever._faiss_index = FaissHNSWIndex.load(faiss_dir)
            retriever.index_backend = "faiss_hnsw"
        return retriever

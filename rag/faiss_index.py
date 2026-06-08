from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag.chunker import Chunk


def is_faiss_available() -> bool:
    try:
        import faiss  # type: ignore[import-not-found]
    except Exception:
        return False
    return True


@dataclass
class FaissHNSWIndex:
    dimension: int
    chunks: list[Chunk]
    index: Any
    metric: str = "ip"

    @classmethod
    def build_index(
        cls,
        vectors: list[list[float]],
        chunks: list[Chunk],
        m: int = 32,
        metric: str = "ip",
    ) -> "FaissHNSWIndex":
        if not is_faiss_available():
            raise RuntimeError("faiss is not installed; install faiss-cpu to use IndexHNSWFlat")

        import faiss  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]

        if not vectors:
            raise ValueError("vectors must not be empty")
        if len(vectors) != len(chunks):
            raise ValueError("vectors and chunks must have the same length")

        dimension = len(vectors[0])
        matrix = np.asarray(vectors, dtype="float32")
        if metric == "ip":
            faiss.normalize_L2(matrix)
            index = faiss.IndexHNSWFlat(dimension, m)
            index.metric_type = faiss.METRIC_INNER_PRODUCT
        else:
            index = faiss.IndexHNSWFlat(dimension, m)
        index.hnsw.efSearch = max(32, m * 2)
        index.hnsw.efConstruction = max(64, m * 4)
        index.add(matrix)
        return cls(dimension=dimension, chunks=list(chunks), index=index, metric=metric)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        if not is_faiss_available():
            raise RuntimeError("faiss is not installed; cannot search IndexHNSWFlat")

        import faiss  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]

        if len(query_vector) != self.dimension:
            raise ValueError("query vector dimension mismatch")

        query = np.asarray([query_vector], dtype="float32")
        if self.metric == "ip":
            faiss.normalize_L2(query)
        scores, indices = self.index.search(query, top_k)
        results: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.chunks[int(idx)]
            results.append(
                {
                    "chunk": chunk,
                    "score": float(score),
                }
            )
        return results

    def save(self, path: str | Path) -> Path:
        root = Path(path)
        root.mkdir(parents=True, exist_ok=True)
        meta_path = root / "metadata.json"
        index_path = root / "index.faiss"
        chunks_path = root / "chunks.pkl"

        if not is_faiss_available():
            raise RuntimeError("faiss is not installed; cannot save IndexHNSWFlat")

        import faiss  # type: ignore[import-not-found]

        faiss.write_index(self.index, str(index_path))
        chunks_path.write_bytes(pickle.dumps(self.chunks))
        meta_path.write_text(
            json.dumps(
                {
                    "dimension": self.dimension,
                    "metric": self.metric,
                    "index_path": index_path.name,
                    "chunks_path": chunks_path.name,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return root

    @classmethod
    def load(cls, path: str | Path) -> "FaissHNSWIndex":
        root = Path(path)
        meta = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        if not is_faiss_available():
            raise RuntimeError("faiss is not installed; cannot load IndexHNSWFlat")

        import faiss  # type: ignore[import-not-found]

        index = faiss.read_index(str(root / meta["index_path"]))
        chunks = pickle.loads((root / meta["chunks_path"]).read_bytes())
        return cls(
            dimension=int(meta["dimension"]),
            chunks=chunks,
            index=index,
            metric=meta.get("metric", "ip"),
        )

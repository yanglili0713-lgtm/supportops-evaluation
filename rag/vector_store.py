from __future__ import annotations

import math
from collections import Counter

from rag.chunker import Chunk
from rag.retriever import RetrievalResult, tokenize


SEMANTIC_ALIASES = {
    "导入": ["上传", "写入"],
    "文档": ["pdf", "知识库"],
    "资料": ["文档", "知识库"],
    "答案": ["检索", "召回"],
    "没有依据": ["检索不到", "召回不到"],
    "找不到": ["检索不到", "搜不到"],
    "失效": ["invalid", "过期"],
    "密钥": ["api", "key"],
    "鉴权": ["api", "key", "权限"],
}


class SimpleVectorStore:
    """In-memory token vector store with cosine similarity."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.vectors: list[Counter[str]] = []

    def add_chunks(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)
        self.vectors.extend(_vectorize(chunk.text) for chunk in chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_vector = _vectorize(query)
        if not query_vector:
            return []

        results = []
        for chunk, vector in zip(self.chunks, self.vectors):
            score = _cosine(query_vector, vector)
            if score <= 0:
                continue
            results.append(
                RetrievalResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    source=chunk.source,
                    text=chunk.text,
                    score=score,
                )
            )

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]


def _vectorize(text: str) -> Counter[str]:
    tokens = tokenize(text)
    expanded = list(tokens)
    compact_text = text.lower().replace(" ", "")
    for phrase, aliases in SEMANTIC_ALIASES.items():
        if phrase.replace(" ", "") in compact_text:
            expanded.extend(aliases)
    return Counter(expanded)


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    if numerator == 0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm)

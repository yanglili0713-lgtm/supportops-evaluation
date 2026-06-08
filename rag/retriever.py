from __future__ import annotations

import math
import re
from dataclasses import dataclass

from rag.chunker import Chunk


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """Tokenize mixed Chinese/English text.

    English and numbers are kept as word-level tokens, while Chinese is split
    into single-character tokens. This simple strategy is enough for the MVP
    and avoids failed recall when users omit spaces, e.g. "上传PDF后".
    """
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: str
    doc_id: str
    source: str
    text: str
    score: float
    bm25_score: float | None = None
    dense_score: float | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(chunk.text) for chunk in chunks]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 0.0
        self.df = self._build_df()

    def _build_df(self) -> dict[str, int]:
        df: dict[str, int] = {}
        for tokens in self.doc_tokens:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        return df

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        scored: list[RetrievalResult] = []
        for chunk, tokens, doc_len in zip(self.chunks, self.doc_tokens, self.doc_lens):
            score = self._score(query_tokens, tokens, doc_len)
            if score > 0:
                scored.append(
                    RetrievalResult(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        source=chunk.source,
                        text=chunk.text,
                        score=score,
                        bm25_score=score,
                    )
                )

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def _score(self, query_tokens: list[str], doc_tokens: list[str], doc_len: int) -> float:
        n_docs = len(self.chunks)
        tf: dict[str, int] = {}
        for token in doc_tokens:
            tf[token] = tf.get(token, 0) + 1

        score = 0.0
        for token in query_tokens:
            if token not in tf:
                continue
            df = self.df.get(token, 0)
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            freq = tf[token]
            denom = freq + self.k1 * (1 - self.b + self.b * doc_len / (self.avgdl or 1))
            score += idf * (freq * (self.k1 + 1)) / denom
        return score

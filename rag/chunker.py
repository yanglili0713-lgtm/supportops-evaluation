from __future__ import annotations

from dataclasses import dataclass

from rag.ingest import Document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    source: str
    text: str


def chunk_documents(
    docs: list[Document],
    chunk_size: int = 450,
    chunk_overlap: int = 80,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")

    chunks: list[Chunk] = []
    for doc in docs:
        start = 0
        index = 0
        while start < len(doc.text):
            end = start + chunk_size
            text = doc.text[start:end].strip()
            if text:
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.doc_id}:{index}",
                        doc_id=doc.doc_id,
                        source=doc.source,
                        text=text,
                    )
                )
            index += 1
            start += chunk_size - chunk_overlap

    return chunks

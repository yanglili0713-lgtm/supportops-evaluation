from __future__ import annotations

from rag.chunker import chunk_documents
from rag.ingest import load_markdown_docs
from rag.retriever import BM25Retriever, RetrievalResult


class RAGPipeline:
    def __init__(self, docs_dir: str = "data/docs") -> None:
        docs = load_markdown_docs(docs_dir)
        chunks = chunk_documents(docs)
        self.retriever = BM25Retriever(chunks)

    def query(self, question: str, top_k: int = 3) -> list[RetrievalResult]:
        return self.retriever.search(question, top_k=top_k)

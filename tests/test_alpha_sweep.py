from __future__ import annotations

import csv
from pathlib import Path

import evals.supportops_retrieval_eval as supportops_eval
import rag.dense_retriever as dense_module
import rag.reranker as reranker_module
from rag.chunker import chunk_documents
from rag.dense_retriever import DenseEmbeddingRetriever, FallbackTokenEmbeddingBackend
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import Document, load_markdown_docs
from rag.retriever import BM25Retriever
from scripts.run_ablation import build_parser, parse_alpha_sweep


def test_run_ablation_help_exposes_alpha_sweep():
    help_text = build_parser().format_help()
    assert "--alpha-sweep" in help_text
    assert "more BM25-weighted" in help_text


def test_parse_alpha_sweep_parses_commas():
    assert parse_alpha_sweep("0,0.2,1.0") == [0.0, 0.2, 1.0]


def test_alpha_sweep_generates_summary_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dense_module,
        "load_embedding_backend",
        lambda model_name=None, allow_fallback=True, **kwargs: FallbackTokenEmbeddingBackend(),
    )
    monkeypatch.setattr(reranker_module, "_load_cross_encoder", lambda model_name=None: None)

    docs = [
        Document(doc_id=item.doc_id, source=item.source, text=item.text)
        for item in load_markdown_docs("data/docs")
    ]
    chunks = chunk_documents(docs, chunk_size=120, chunk_overlap=10)
    bm25 = BM25Retriever(chunks)
    dense = DenseEmbeddingRetriever(chunks, allow_fallback=True)
    hybrid = HybridRetriever(chunks, alpha=0.6, bm25=bm25, dense=dense)
    bundle = supportops_eval.SearchBundle(chunks=chunks, bm25=bm25, dense=dense, hybrid=hybrid)

    monkeypatch.setattr(
        supportops_eval,
        "_build_search_bundle",
        lambda docs_dir, chunk_size, chunk_overlap: bundle,
    )

    result = supportops_eval.run_supportops_alpha_sweep(
        alphas=[0.0, 1.0],
        output_dir=tmp_path,
        max_cases=3,
    )

    csv_path = tmp_path / "alpha_sweep_summary.csv"
    json_path = tmp_path / "alpha_sweep_summary.json"

    assert csv_path.exists()
    assert json_path.exists()
    assert len(result["rows"]) == 2

    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert rows
    expected_fields = {
        "alpha",
        "mrr_at_10",
        "top1_evidence_precision",
        "latency_p95_ms",
        "dense_backend",
        "reranker_backend",
        "fallback_used",
    }
    assert expected_fields.issubset(rows[0])

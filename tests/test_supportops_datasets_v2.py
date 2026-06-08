from __future__ import annotations

from pathlib import Path

import pytest

from evals.supportops_datasets import load_banking77, load_supportops_bench, load_supportops_docs


def test_supportops_bench_loader_upgrades_schema():
    cases = load_supportops_bench()

    assert len(cases) == 80
    first = cases[0]
    assert {"id", "query", "intent", "difficulty", "gold_doc_ids", "gold_answer", "no_answer", "tags"}.issubset(first)
    assert isinstance(first["gold_doc_ids"], list)
    assert isinstance(first["tags"], list)


def test_supportops_docs_loader_returns_seed_schema():
    docs = load_supportops_docs()

    assert docs
    first = docs[0]
    assert {"doc_id", "title", "text", "source", "tags"}.issubset(first)
    assert first["source"] == "supportops_seed"


def test_banking77_loader_sample_fixture_works():
    rows = load_banking77(sample_path=Path("data/banking77_sample.jsonl"), max_samples=3, allow_fallback=False)

    assert len(rows) == 3
    assert rows[0]["query"]
    assert rows[0]["intent"]


def test_banking77_loader_can_fail_cleanly_without_datasets():
    with pytest.raises(RuntimeError):
        load_banking77(allow_download=False, allow_fallback=False)

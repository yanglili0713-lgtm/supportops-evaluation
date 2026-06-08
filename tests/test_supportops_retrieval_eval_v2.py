from __future__ import annotations

import json

from evals.supportops_retrieval_eval import (
    _mrr_at_k,
    _ndcg_at_k,
    _refusal_metrics,
    run_supportops_retrieval_eval,
)


def test_ranking_and_refusal_metrics_are_computed_correctly():
    assert _mrr_at_k(["doc_a", "doc_b"], ["doc_b"], 10) == 0.5
    assert _ndcg_at_k(["doc_a", "doc_b"], ["doc_b"], 10) == 0.6309

    metrics = _refusal_metrics(
        [
            {"no_answer": True, "refusal_decision": True},
            {"no_answer": True, "refusal_decision": False},
            {"no_answer": False, "refusal_decision": False},
            {"no_answer": False, "refusal_decision": True},
        ]
    )
    assert metrics["accuracy"] == 0.5
    assert metrics["f1"] == 0.5


def test_supportops_retrieval_eval_writes_trace_schema(tmp_path):
    result = run_supportops_retrieval_eval(
        methods=["bm25", "hybrid"],
        output_dir=tmp_path,
        max_cases=3,
    )

    trace_path = tmp_path / "trace.jsonl"
    failure_path = tmp_path / "failure_cases.jsonl"
    summary_path = tmp_path / "retrieval_summary.json"

    assert trace_path.exists()
    assert failure_path.exists()
    assert summary_path.exists()

    trace_row = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
    expected_fields = {
        "case_id",
        "query",
        "method",
        "intent",
        "retrieved_doc_ids",
        "gold_doc_ids",
        "retrieved_evidence",
        "hit_at_5",
        "hit_at_10",
        "mrr_at_10",
        "latency_ms",
        "planner_decision",
        "refusal_decision",
        "failure_reason",
    }
    assert expected_fields.issubset(trace_row)
    assert "bm25" in result["methods"]
    assert "hybrid" in result["methods"]

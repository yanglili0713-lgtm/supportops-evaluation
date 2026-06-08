from __future__ import annotations

from pathlib import Path

from app.streamlit_app import find_existing_path, read_jsonl, read_metric_file, run_demo_query


def test_streamlit_helpers_handle_missing_files(tmp_path):
    missing_jsonl = tmp_path / "missing.jsonl"
    missing_csv = tmp_path / "missing.csv"

    assert read_jsonl(missing_jsonl) == []
    assert read_metric_file(missing_csv) == []
    assert find_existing_path([missing_jsonl, missing_csv]) is None


def test_demo_query_returns_deterministic_answer_and_trace():
    result = run_demo_query("API Key 失效了，接口一直返回 unauthorized", "bm25", 5)

    assert result["answer"].startswith("Deterministic demo answer:")
    assert result["router_result"]["intent"] == "api_key_issue"
    assert set(result["trace"]) >= {
        "case_id",
        "query",
        "method",
        "intent",
        "retrieved_doc_ids",
        "gold_doc_ids",
        "planner_decision",
        "refusal_decision",
        "failure_reason",
    }

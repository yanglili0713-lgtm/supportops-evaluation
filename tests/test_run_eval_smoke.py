import json
from pathlib import Path

from run_eval import DEFAULT_PIPELINES, run_all_pipelines


def test_run_eval_generates_unified_outputs(tmp_path):
    out_dir = tmp_path / "reports"
    trace_dir = tmp_path / "traces"

    report = run_all_pipelines(out_dir=out_dir, trace_dir=trace_dir)

    report_path = out_dir / "report.json"
    trace_path = trace_dir / "trace.jsonl"
    failure_path = out_dir / "failure_analysis.md"

    assert report_path.exists()
    assert trace_path.exists()
    assert failure_path.exists()
    assert set(DEFAULT_PIPELINES).issubset(report["pipelines"])

    persisted_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert set(DEFAULT_PIPELINES).issubset(persisted_report["pipelines"])

    trace_lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert trace_lines

    first_trace = json.loads(trace_lines[0])
    expected_fields = {
        "case_id",
        "pipeline",
        "query",
        "gold_intent",
        "route_intent",
        "expected_doc_ids",
        "retrieved_doc_ids",
        "answerability",
        "refusal_decision",
        "metrics",
        "latency_ms",
        "decision_notes",
    }
    assert expected_fields.issubset(first_trace)
    assert "Latency tradeoff" in failure_path.read_text(encoding="utf-8")

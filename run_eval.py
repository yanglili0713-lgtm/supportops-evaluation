from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from evals.failure_analysis import generate_failure_analysis
from evals.supportops_adapters import run_pipeline
from evals.supportops_metrics import aggregate, refusal_correct, score_case
from evals.supportops_run_eval import DEFAULT_BENCH_PATH, load_bench


DEFAULT_PIPELINES = ["dummy", "naive", "hybrid", "graph", "planner"]


def run_all_pipelines(
    bench_path: str | Path = DEFAULT_BENCH_PATH,
    pipelines: list[str] | None = None,
    out_dir: str | Path = "reports",
    trace_dir: str | Path = "traces",
    force_fallback_embedding: bool | None = None,
) -> dict[str, Any]:
    selected_pipelines = pipelines or DEFAULT_PIPELINES
    cases = load_bench(bench_path)
    out_path = Path(out_dir)
    trace_path = Path(trace_dir)
    report_file = out_path / "report.json"
    trace_file = trace_path / "trace.jsonl"
    failure_file = out_path / "failure_analysis.md"

    out_path.mkdir(parents=True, exist_ok=True)
    trace_path.mkdir(parents=True, exist_ok=True)

    pipeline_reports: dict[str, Any] = {}
    trace_records: list[dict[str, Any]] = []

    with trace_file.open("w", encoding="utf-8") as trace_handle:
        for pipeline_name in selected_pipelines:
            scores = []
            errors = []
            for case in cases:
                normalized_case = normalize_case(case)
                started = time.perf_counter()
                error = None
                prediction = {"answer": "", "retrieved_docs": [], "route": None, "raw": {}}
                try:
                    prediction = run_pipeline(
                        pipeline_name,
                        case["query"],
                        force_fallback_embedding=force_fallback_embedding,
                    )
                except Exception as exc:  # noqa: BLE001 - eval should continue per case.
                    error = str(exc)
                    errors.append({"case_id": normalized_case["case_id"], "error": error})

                latency_ms = (time.perf_counter() - started) * 1000
                prediction["latency_ms"] = latency_ms
                case_score = score_case(case, prediction)
                case_score["latency_ms"] = latency_ms
                scores.append(case_score)

                trace_record = build_trace_record(
                    case=normalized_case,
                    pipeline_name=pipeline_name,
                    prediction=prediction,
                    metrics=case_score,
                    latency_ms=latency_ms,
                    error=error,
                )
                trace_records.append(trace_record)
                trace_handle.write(json.dumps(trace_record, ensure_ascii=False) + "\n")

            summary = aggregate(scores, pipeline_name=pipeline_name)
            pipeline_reports[pipeline_name] = summarize_pipeline(summary, errors)

    report = {
        "project": "SupportOps Evaluation",
        "benchmark": {
            "path": str(bench_path),
            "case_count": len(cases),
            "schema_adapter": "evals/supportops_bench.yaml is mapped to unified SupportOps Evaluation fields at runtime",
        },
        "pipelines": pipeline_reports,
        "outputs": {
            "report": str(report_file),
            "trace": str(trace_file),
            "failure_analysis": str(failure_file),
        },
    }
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    generate_failure_analysis(report_path=report_file, trace_path=trace_file, out_path=failure_file)
    return report


def normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    should_refuse = bool(case.get("should_refuse", False))
    task_type = case.get("task_type", "")
    gold_intent = case.get("expected_route") or task_type
    tags = build_tags(case, should_refuse=should_refuse, gold_intent=gold_intent)

    return {
        "case_id": case.get("id"),
        "query": case.get("query", ""),
        "intent": task_type,
        "gold_intent": gold_intent,
        "expected_doc_ids": case.get("expected_docs", []),
        "answerability": "no_answer" if should_refuse else "answerable",
        "difficulty": case.get("difficulty", ""),
        "seen_split": case.get("split", ""),
        "multi_doc": bool(case.get("requires_multi_doc", False)),
        "tags": tags,
        "should_refuse": should_refuse,
    }


def build_tags(case: dict[str, Any], should_refuse: bool, gold_intent: str) -> list[str]:
    tags = {
        str(case.get("task_type", "")).strip(),
        str(gold_intent).strip(),
        str(case.get("difficulty", "")).strip(),
        str(case.get("split", "")).strip(),
    }
    if case.get("requires_multi_doc"):
        tags.add("multi_doc")
    if should_refuse:
        tags.add("no_answer")
    if case.get("task_type") == "security_boundary":
        tags.add("security_boundary")
    return sorted(tag for tag in tags if tag)


def build_trace_record(
    case: dict[str, Any],
    pipeline_name: str,
    prediction: dict[str, Any],
    metrics: dict[str, Any],
    latency_ms: float,
    error: str | None,
) -> dict[str, Any]:
    answer = prediction.get("answer", "")
    route_intent = prediction.get("route")
    should_refuse = bool(case.get("should_refuse", False))
    refusal_decision = not refusal_correct(answer, should_refuse) if not should_refuse else refusal_correct(answer, True)
    notes = decision_notes(prediction=prediction, error=error)

    return {
        "case_id": case["case_id"],
        "pipeline": pipeline_name,
        "query": case["query"],
        "gold_intent": case["gold_intent"],
        "route_intent": route_intent,
        "expected_doc_ids": case["expected_doc_ids"],
        "retrieved_doc_ids": prediction.get("retrieved_docs", []),
        "answerability": case["answerability"],
        "refusal_decision": refusal_decision,
        "metrics": {
            "evidence_recall_at_5": metrics.get("evidence_recall_at_5"),
            "evidence_precision_at_5": metrics.get("evidence_precision_at_5"),
            "refusal_accuracy": metrics.get("refusal_accuracy"),
            "route_accuracy": metrics.get("route_accuracy"),
        },
        "latency_ms": round(latency_ms, 4),
        "decision_notes": notes,
        "tags": case["tags"],
        "error": error,
    }


def decision_notes(prediction: dict[str, Any], error: str | None) -> list[str]:
    notes = []
    if error:
        notes.append(f"error: {error}")
    raw = prediction.get("raw", {}) or {}
    if raw.get("mapping_reason"):
        notes.append(raw["mapping_reason"])
    if raw.get("warnings"):
        notes.extend(str(warning) for warning in raw["warnings"])
    if raw.get("plan", {}).get("reason"):
        notes.append(raw["plan"]["reason"])
    if not notes:
        notes.append(f"pipeline={raw.get('pipeline', 'unknown')}")
    return notes


def summarize_pipeline(summary: dict[str, Any], errors: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "case_count": summary.get("cases", 0),
        "evidence_recall_at_5": summary.get("avg_evidence_recall_at_5"),
        "evidence_precision_at_5": summary.get("avg_evidence_precision_at_5"),
        "refusal_accuracy": summary.get("avg_refusal_accuracy"),
        "route_accuracy": summary.get("avg_route_accuracy"),
        "average_latency_ms": summary.get("latency_ms", {}).get("avg", 0.0),
        "latency_ms": summary.get("latency_ms", {}),
        "errors": errors,
    }


def parse_pipelines(value: str) -> list[str]:
    pipelines = [item.strip() for item in value.split(",") if item.strip()]
    return pipelines or DEFAULT_PIPELINES


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SupportOps Evaluation across pipelines.")
    parser.add_argument("--bench", default=str(DEFAULT_BENCH_PATH))
    parser.add_argument("--pipelines", default=",".join(DEFAULT_PIPELINES))
    parser.add_argument("--out-dir", default="reports")
    parser.add_argument("--trace-dir", default="traces")
    parser.add_argument(
        "--embedding-backend",
        choices=["fallback", "real"],
        default="fallback",
        help="Use fallback to keep tests offline, or real embeddings when you want to benchmark them.",
    )
    args = parser.parse_args()

    report = run_all_pipelines(
        bench_path=args.bench,
        pipelines=parse_pipelines(args.pipelines),
        out_dir=args.out_dir,
        trace_dir=args.trace_dir,
        force_fallback_embedding=args.embedding_backend == "fallback",
    )
    print(json.dumps(report["pipelines"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_failure_analysis(
    report_path: str | Path = "reports/report.json",
    trace_path: str | Path = "traces/trace.jsonl",
    out_path: str | Path = "reports/failure_analysis.md",
) -> str:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    traces = load_traces(trace_path)
    content = render_failure_analysis(report, traces)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(content, encoding="utf-8")
    return content


def load_traces(path: str | Path) -> list[dict[str, Any]]:
    records = []
    trace_file = Path(path)
    if not trace_file.exists():
        return records
    for line in trace_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def render_failure_analysis(report: dict[str, Any], traces: list[dict[str, Any]]) -> str:
    pipelines = report.get("pipelines", {})
    lines = [
        "# Failure Analysis",
        "",
        "## Overview",
        "",
        f"- Benchmark cases: {report.get('benchmark', {}).get('case_count', 0)}",
        f"- Pipelines: {', '.join(pipelines)}",
        f"- Trace rows: {len(traces)}",
        "",
        _summary_table(pipelines),
        "",
        "## Dummy: rule-aligned sanity baseline",
        "",
        _dummy_explanation(pipelines.get("dummy", {})),
        "",
        "## Naive/Hybrid: high recall but low precision cases",
        "",
        _high_recall_low_precision(traces),
        "",
        "## GraphRAG: evidence concentration analysis",
        "",
        _graph_concentration(traces, pipelines.get("graph", {})),
        "",
        "## Planner: route generalization failures",
        "",
        _planner_route_failures(traces),
        "",
        "## No-answer / security boundary refusal failures",
        "",
        _refusal_failures(traces),
        "",
        "## Latency tradeoff",
        "",
        _latency_tradeoff(pipelines),
        "",
        "## Next optimization plan",
        "",
        "- Add source_doc/source_span metadata to graph evidence to improve document-level grounding.",
        "- Add route-confusion slices for mixed-intent and paraphrased cases before changing router rules.",
        "- Improve no-answer/security refusal with explicit decision fields instead of answer-text marker matching.",
        "- Tune top-k evidence aggregation to reduce naive/hybrid retrieval noise while preserving recall.",
        "- Keep planner deterministic and local; only add heavier components after the benchmark exposes a concrete gap.",
        "",
    ]
    return "\n".join(lines)


def _summary_table(pipelines: dict[str, Any]) -> str:
    rows = [
        "| Pipeline | Cases | Recall@5 | Precision@5 | Refusal Acc | Route Acc | Avg Latency ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in pipelines.items():
        rows.append(
            "| {name} | {cases} | {recall} | {precision} | {refusal} | {route} | {latency} |".format(
                name=name,
                cases=summary.get("case_count", 0),
                recall=_fmt(summary.get("evidence_recall_at_5")),
                precision=_fmt(summary.get("evidence_precision_at_5")),
                refusal=_fmt(summary.get("refusal_accuracy")),
                route=_fmt(summary.get("route_accuracy")),
                latency=_fmt(summary.get("average_latency_ms")),
            )
        )
    return "\n".join(rows)


def _dummy_explanation(summary: dict[str, Any]) -> str:
    if not summary:
        return "Dummy pipeline was not included in this run."

    return "\n".join(
        [
            f"Dummy Recall@5 is {_fmt(summary.get('evidence_recall_at_5'))} and Precision@5 is {_fmt(summary.get('evidence_precision_at_5'))}.",
            "This pipeline is a rule-based sanity baseline, not a weak baseline and not an oracle baseline.",
            "It does not read expected_docs, gold labels, or benchmark answers. Its high score comes from hand-written rules and document taxonomy that are intentionally aligned with the local SupportOps seed benchmark.",
            "Use dummy only to verify that the evaluation harness, schema adapter, metrics, trace writing, and report generation are working.",
        ]
    )


def _high_recall_low_precision(traces: list[dict[str, Any]]) -> str:
    rows = []
    for record in traces:
        if record.get("pipeline") not in {"naive", "hybrid"}:
            continue
        metrics = record.get("metrics", {})
        recall = metrics.get("evidence_recall_at_5")
        precision = metrics.get("evidence_precision_at_5")
        if recall == 1.0 and precision is not None and precision < 0.5:
            rows.append(record)

    if not rows:
        return "No high-recall low-precision naive/hybrid cases were found."

    by_pipeline = _count_by(rows, "pipeline")
    examples = _examples(rows, fields=["pipeline", "case_id", "gold_intent", "retrieved_doc_ids"], limit=5)
    overlap = _naive_hybrid_doc_set_overlap(traces)
    return "\n".join(
        [
            f"Found {len(rows)} cases where naive/hybrid retrieved all expected evidence but mixed in noisy top-k documents.",
            f"Counts by pipeline: {_format_counts(by_pipeline)}.",
            overlap,
            "When naive and hybrid have identical doc-level metrics, it usually means the current 5-doc seed corpus and doc-source-level @5 evaluation are too coarse to expose chunk/ranking/score differences.",
            "",
            examples,
        ]
    )


def _graph_concentration(traces: list[dict[str, Any]], graph_summary: dict[str, Any]) -> str:
    graph_rows = [record for record in traces if record.get("pipeline") == "graph"]
    if not graph_rows:
        return "No GraphRAG traces were found."

    precision_values = [
        record["metrics"]["evidence_precision_at_5"]
        for record in graph_rows
        if record.get("metrics", {}).get("evidence_precision_at_5") is not None
    ]
    concentrated = [
        record
        for record in graph_rows
        if (record.get("metrics", {}).get("evidence_precision_at_5") or 0.0) >= 0.8
    ]
    missed = [
        record
        for record in graph_rows
        if (record.get("metrics", {}).get("evidence_recall_at_5") or 0.0) < 1.0
        and record.get("expected_doc_ids")
    ]
    avg_precision = sum(precision_values) / len(precision_values) if precision_values else 0.0
    examples = _examples(missed, fields=["case_id", "gold_intent", "expected_doc_ids", "retrieved_doc_ids"], limit=5)

    return "\n".join(
        [
            f"GraphRAG average precision@5 is {_fmt(graph_summary.get('evidence_precision_at_5', avg_precision))}; {len(concentrated)} of {len(graph_rows)} cases have precision@5 >= 0.8.",
            f"Recall misses with expected evidence: {len(missed)}.",
            "This indicates concentrated evidence when graph/entity signals fire, but incomplete coverage for paraphrased or weakly linked cases.",
            "Interpret this as an evidence-concentration tradeoff from a lightweight in-memory graph retrieval layer, not as production GraphRAG coverage.",
            "",
            examples,
        ]
    )


def _planner_route_failures(traces: list[dict[str, Any]]) -> str:
    failures = [
        record
        for record in traces
        if record.get("pipeline") == "planner"
        and record.get("metrics", {}).get("route_accuracy") == 0.0
    ]
    if not failures:
        return "No planner route failures were found."

    by_gold = _count_by(failures, "gold_intent")
    examples = _examples(failures, fields=["case_id", "gold_intent", "route_intent", "query"], limit=8)
    return "\n".join(
        [
            f"Found {len(failures)} planner route failures.",
            f"Gold intent distribution: {_format_counts(by_gold)}.",
            "The planner is a demo-level deterministic planner. These failures expose route generalization limits from keyword-driven routing, especially for weak expressions, mixed symptoms, and cases where extracted entities do not directly imply the final route.",
            "",
            examples,
        ]
    )


def _refusal_failures(traces: list[dict[str, Any]]) -> str:
    failures = [
        record
        for record in traces
        if ("no_answer" in record.get("tags", []) or "security_boundary" in record.get("tags", []))
        and record.get("metrics", {}).get("refusal_accuracy") == 0.0
    ]
    if not failures:
        return "No no-answer/security refusal failures were found."

    by_pipeline = _count_by(failures, "pipeline")
    examples = _examples(failures, fields=["pipeline", "case_id", "gold_intent", "answerability", "query"], limit=8)
    return "\n".join(
        [
            f"Found {len(failures)} no-answer/security refusal failures.",
            f"Counts by pipeline: {_format_counts(by_pipeline)}.",
            "Refusal Accuracy is currently a marker-based baseline safety metric. It checks whether outputs contain refusal-like text; it is not a strict safety verifier or answer-faithfulness proof.",
            "",
            examples,
        ]
    )


def _naive_hybrid_doc_set_overlap(traces: list[dict[str, Any]]) -> str:
    by_case: dict[tuple[str, str], dict[str, Any]] = {
        (record.get("pipeline"), record.get("case_id")): record
        for record in traces
        if record.get("pipeline") in {"naive", "hybrid"}
    }
    case_ids = sorted({case_id for pipeline, case_id in by_case if pipeline in {"naive", "hybrid"}})
    comparable = 0
    same_set = 0
    same_order = 0
    for case_id in case_ids:
        naive = by_case.get(("naive", case_id))
        hybrid = by_case.get(("hybrid", case_id))
        if not naive or not hybrid:
            continue
        comparable += 1
        naive_docs = naive.get("retrieved_doc_ids", [])
        hybrid_docs = hybrid.get("retrieved_doc_ids", [])
        if naive_docs == hybrid_docs:
            same_order += 1
        if set(naive_docs) == set(hybrid_docs):
            same_set += 1

    if comparable == 0:
        return "No comparable naive/hybrid traces were found."
    return (
        f"Naive/hybrid retrieved_doc_ids overlap: same doc set in {same_set}/{comparable} cases; "
        f"same ordered list in {same_order}/{comparable} cases."
    )


def _latency_tradeoff(pipelines: dict[str, Any]) -> str:
    if not pipelines:
        return "No latency data found."
    ordered = sorted(
        pipelines.items(),
        key=lambda item: item[1].get("average_latency_ms") or 0.0,
        reverse=True,
    )
    rows = [
        f"- {name}: avg={_fmt(summary.get('average_latency_ms'))} ms, p95={_fmt(summary.get('latency_ms', {}).get('p95'))} ms"
        for name, summary in ordered
    ]
    slowest = ordered[0][0]
    fastest = ordered[-1][0]
    return "\n".join(
        [
            f"Slowest pipeline: {slowest}. Fastest pipeline: {fastest}. Planner is expected to cost more because it runs routing, planning, retrieval, optional graph/tool steps, verification, and trace recording.",
            "",
            *rows,
        ]
    )


def _examples(records: list[dict[str, Any]], fields: list[str], limit: int) -> str:
    if not records:
        return "No example cases."
    lines = []
    for record in records[:limit]:
        parts = [f"{field}={record.get(field)}" for field in fields]
        lines.append(f"- {'; '.join(parts)}")
    return "\n".join(lines)


def _count_by(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get(field))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items()) or "none"


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    generate_failure_analysis()

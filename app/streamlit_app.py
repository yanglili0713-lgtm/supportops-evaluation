from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.evidence_planner import plan_retrieval
from app.memory import CaseState, update_case_state
from app.router import route_question
from app.skill_selector import select_skill
from app.verifier import evidence_sufficiency_check
from evals.supportops_datasets import (
    SUPPORTOPS_INTENT_ANSWERS,
    load_supportops_bench,
    load_supportops_docs,
)
from evals.supportops_retrieval_eval import (
    REFUSAL_THRESHOLDS,
    _build_search_bundle,
    _hybrid_search,
    _planner_search,
    _should_refuse,
)


DEFAULT_SUPPORTOPS_BENCH = Path("evals/supportops_bench.yaml")
DEFAULT_DOCS_DIR = Path("data/docs")
SUMMARY_CANDIDATES = [
    Path("runs/eval/retrieval_summary.csv"),
    Path("runs/eval_smoke/retrieval_summary.csv"),
]
ABLATION_CANDIDATES = [
    Path("runs/eval/ablation_summary.csv"),
    Path("runs/eval_smoke/ablation_summary.csv"),
]
FAILURE_CANDIDATES = [
    Path("runs/eval/failure_cases.jsonl"),
    Path("runs/eval_smoke/failure_cases.jsonl"),
]
METHODS = ["bm25", "hybrid", "hybrid_reranker", "planner"]
TOP_K_CHOICES = [5, 10, 30]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def read_metric_file(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    if file_path.suffix.lower() == ".jsonl":
        return read_jsonl(file_path)
    if file_path.suffix.lower() == ".json":
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []
    if file_path.suffix.lower() == ".csv":
        with file_path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    return []


def find_existing_path(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def normalize_query(text: str) -> str:
    return " ".join((text or "").lower().split())


@lru_cache(maxsize=1)
def _doc_title_map() -> dict[str, str]:
    return {item["doc_id"]: item["title"] for item in load_supportops_docs(DEFAULT_DOCS_DIR)}


@lru_cache(maxsize=1)
def _supportops_case_index() -> dict[str, dict[str, Any]]:
    return {normalize_query(case["query"]): case for case in load_supportops_bench(DEFAULT_SUPPORTOPS_BENCH)}


@lru_cache(maxsize=1)
def _search_bundle():
    return _build_search_bundle(DEFAULT_DOCS_DIR, chunk_size=512, chunk_overlap=80)


def build_deterministic_answer(
    query: str,
    intent: str,
    evidence_rows: list[dict[str, Any]],
    refusal_decision: bool,
    matched_case: dict[str, Any] | None = None,
) -> str:
    if refusal_decision:
        return (
            "Deterministic demo answer: no reliable answer is available from the current "
            "evidence. Please provide more context or escalate."
        )

    if matched_case and matched_case.get("gold_answer"):
        return f"Deterministic demo answer: {matched_case['gold_answer']}"

    evidence_bits = []
    for row in evidence_rows[:2]:
        snippet = row["snippet"].replace("\n", " ").strip()
        evidence_bits.append(f"{row['doc_id']}: {snippet[:140]}")

    base = SUPPORTOPS_INTENT_ANSWERS.get(intent, SUPPORTOPS_INTENT_ANSWERS["unknown"])
    if evidence_bits:
        joined = " | ".join(evidence_bits)
        return f"Deterministic demo answer: {base} Evidence: {joined}"
    return f"Deterministic demo answer: {base}"


def run_demo_query(query: str, method: str, top_k: int) -> dict[str, Any]:
    router_result = route_question(query)
    case_state = CaseState()
    update_case_state(case_state, query, router_result=router_result)
    selected_skill = select_skill(router_result["intent"])
    plan = plan_retrieval(query, case_state, router_result, selected_skill)
    bundle = _search_bundle()
    matched_case = _supportops_case_index().get(normalize_query(query))

    if method == "bm25":
        results = bundle.bm25.search(query, top_k=top_k)
        planner_decision = "bm25"
    elif method == "hybrid":
        results = _hybrid_search(bundle, query, top_k=top_k, rerank=False)
        planner_decision = "hybrid"
    elif method == "hybrid_reranker":
        results = _hybrid_search(bundle, query, top_k=top_k, rerank=True)
        planner_decision = "hybrid_reranker"
    elif method == "planner":
        results, planner_decision = _planner_search(case_state.to_dict() | {"query": query}, bundle, search_top_k=top_k, method_config={})
    else:
        raise ValueError(f"Unsupported method: {method}")

    retrieved_doc_ids = _unique_doc_ids(results)
    evidence_rows = _format_evidence_rows(results, top_k=top_k)
    search_result = {
        "retrieved": results,
        "top_score": results[0].score if results else 0.0,
        "planner_decision": planner_decision,
    }
    refusal_decision = _should_refuse(
        matched_case or {
            "gold_doc_ids": [],
            "no_answer": False,
            "requires_multi_doc": False,
            "intent": router_result["intent"],
        },
        search_result,
        method if method != "planner" else "planner",
    )
    verification = evidence_sufficiency_check(
        {
            "citations": evidence_rows,
            "graph_evidence": [],
            "tool_calls": [],
            "needs_graph": False,
            "needs_tool": False,
        }
    )
    answer = build_deterministic_answer(query, router_result["intent"], evidence_rows, refusal_decision, matched_case)

    trace = {
        "case_id": matched_case["id"] if matched_case else "demo_query",
        "query": query,
        "method": method,
        "intent": router_result["intent"],
        "retrieved_doc_ids": retrieved_doc_ids,
        "gold_doc_ids": matched_case.get("gold_doc_ids", []) if matched_case else [],
        "hit_at_5": bool(set(retrieved_doc_ids[:5]) & set(matched_case.get("gold_doc_ids", []))) if matched_case else None,
        "hit_at_10": bool(set(retrieved_doc_ids[:10]) & set(matched_case.get("gold_doc_ids", []))) if matched_case else None,
        "mrr_at_10": _mrr_at_10(retrieved_doc_ids, matched_case.get("gold_doc_ids", []) if matched_case else []),
        "latency_ms": None,
        "planner_decision": planner_decision,
        "refusal_decision": refusal_decision,
        "failure_reason": _failure_reason_for_demo(matched_case, retrieved_doc_ids, refusal_decision),
        "verification": verification,
        "selected_skill": selected_skill,
        "plan": plan,
    }

    return {
        "query": query,
        "method": method,
        "router_result": router_result,
        "planner_decision": planner_decision,
        "selected_skill": selected_skill,
        "evidence_rows": evidence_rows,
        "refusal_decision": refusal_decision,
        "answer": answer,
        "trace": trace,
        "matched_case": matched_case,
    }


def _format_evidence_rows(results: list[Any], top_k: int) -> list[dict[str, Any]]:
    title_map = _doc_title_map()
    rows: list[dict[str, Any]] = []
    seen_doc_ids: set[str] = set()
    for rank, result in enumerate(results, start=1):
        if result.doc_id in seen_doc_ids:
            continue
        seen_doc_ids.add(result.doc_id)
        rows.append(
            {
                "rank": len(rows) + 1,
                "doc_id": result.doc_id,
                "title": title_map.get(result.doc_id, result.doc_id.replace("_", " ").title()),
                "score": round(result.score, 4),
                "bm25_score": _format_optional_score(result.bm25_score),
                "dense_score": _format_optional_score(result.dense_score),
                "hybrid_score": _format_optional_score(result.hybrid_score),
                "rerank_score": _format_optional_score(result.rerank_score),
                "snippet": _snippet(result.text, limit=220),
            }
        )
        if len(rows) >= top_k:
            break
    return rows


def _snippet(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit]


def _format_optional_score(value: float | None) -> float | str:
    return round(value, 4) if value is not None else "-"


def _unique_doc_ids(results: list[Any]) -> list[str]:
    ordered: list[str] = []
    for result in results:
        if result.doc_id not in ordered:
            ordered.append(result.doc_id)
    return ordered


def _mrr_at_10(retrieved: list[str], gold: list[str]) -> float | None:
    if not gold:
        return None
    gold_set = set(gold)
    for idx, doc_id in enumerate(retrieved[:10], start=1):
        if doc_id in gold_set:
            return round(1.0 / idx, 4)
    return 0.0


def _failure_reason_for_demo(matched_case: dict[str, Any] | None, retrieved_doc_ids: list[str], refusal_decision: bool) -> str | None:
    if not matched_case:
        return None
    gold = set(matched_case.get("gold_doc_ids", []))
    top10 = set(retrieved_doc_ids[:10])
    if gold and not (gold & top10):
        return "missing_gold_evidence"
    if matched_case.get("no_answer") and not refusal_decision:
        return "should_refuse_but_answered"
    if not matched_case.get("no_answer") and refusal_decision:
        return "should_answer_but_refused"
    return None


def _load_metric_table(paths: list[Path]) -> tuple[Path | None, list[dict[str, Any]]]:
    path = find_existing_path(paths)
    if not path:
        return None, []
    return path, read_metric_file(path)


def _metric_value(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value in (None, ""):
        return "-"
    return str(value)


def _render_demo_tab(st) -> None:
    st.subheader("RAG Demo")
    query = st.text_area("Query", value="API Key 失效了，接口一直返回 unauthorized", height=100)
    method = st.selectbox("Retrieval method", METHODS, index=1)
    top_k = st.slider("top_k", min_value=5, max_value=30, value=10, step=5)

    if st.button("Run Retrieval", type="primary"):
        st.session_state["last_demo_result"] = run_demo_query(query, method, top_k)

    result = st.session_state.get("last_demo_result")
    if not result:
        st.info("Enter a query and run retrieval to inspect evidence, refusal behavior, and trace.")
        return

    st.markdown(f"**Query**: {result['query']}")
    st.markdown(f"**Predicted intent**: `{result['router_result']['intent']}`")
    st.markdown(f"**Planner decision**: `{result['planner_decision']}`")
    st.markdown(f"**Refusal decision**: `{result['refusal_decision']}`")
    st.caption("Deterministic demo answer; no external LLM call is used.")
    st.success(result["answer"])

    if result["evidence_rows"]:
        st.markdown("**Retrieved evidence**")
        st.dataframe(result["evidence_rows"], use_container_width=True, hide_index=True)
    else:
        st.warning("No evidence retrieved.")

    with st.expander("Trace JSON", expanded=False):
        st.code(json.dumps(result["trace"], ensure_ascii=False, indent=2), language="json")


def _render_dashboard_tab(st) -> None:
    st.subheader("Evaluation Dashboard")
    summary_path, summary_rows = _load_metric_table(SUMMARY_CANDIDATES)
    ablation_path, ablation_rows = _load_metric_table(ABLATION_CANDIDATES)

    if not summary_rows:
        st.info(
            "Run the following commands first:\n"
            "python scripts/run_retrieval_eval.py --dataset supportops --methods bm25,hybrid --output-dir runs/eval_smoke\n"
            "python scripts/run_ablation.py --dataset supportops --output-dir runs/eval_smoke"
        )
    else:
        st.caption(f"Loaded retrieval summary: {summary_path}")
        methods = [row.get("method", "") for row in summary_rows if row.get("method")]
        selected_method = st.selectbox("Method", methods, index=0)
        selected_row = next((row for row in summary_rows if row.get("method") == selected_method), summary_rows[0])

        metric_cols = st.columns(4)
        metric_cols[0].metric("Recall@30", _metric_value(selected_row, "recall_at_30"))
        metric_cols[1].metric("MRR@10", _metric_value(selected_row, "mrr_at_10"))
        metric_cols[2].metric("Top-1 precision", _metric_value(selected_row, "top1_evidence_precision"))
        metric_cols[3].metric("P95 latency", f"{_metric_value(selected_row, 'latency_p95_ms')} ms")

        if _metric_value(selected_row, "no_answer_refusal_accuracy") != "-":
            extra_cols = st.columns(2)
            extra_cols[0].metric("Refusal accuracy", _metric_value(selected_row, "no_answer_refusal_accuracy"))
            extra_cols[1].metric("Refusal F1", _metric_value(selected_row, "refusal_f1"))

        st.markdown("**Retrieval summary table**")
        st.dataframe(summary_rows, use_container_width=True, hide_index=True)

    if ablation_rows:
        st.caption(f"Loaded ablation summary: {ablation_path}")
        st.markdown("**Ablation summary table**")
        st.dataframe(ablation_rows, use_container_width=True, hide_index=True)
    else:
        st.info(
            "Ablation summary not found. Run:\n"
            "python scripts/run_ablation.py --dataset supportops --output-dir runs/eval_smoke"
        )


def _render_failure_tab(st) -> None:
    st.subheader("Failure Analysis")
    failure_path, failure_rows = _load_metric_table(FAILURE_CANDIDATES)

    if not failure_rows:
        st.info(
            "Run the following command first:\n"
            "python scripts/run_retrieval_eval.py --dataset supportops --methods bm25,hybrid --output-dir runs/eval_smoke"
        )
        return

    st.caption(f"Loaded failure cases: {failure_path}")
    reasons = sorted({row.get("failure_reason", "unknown") for row in failure_rows if row.get("failure_reason")})
    selected_reason = st.selectbox("failure_reason", ["all"] + reasons)
    filtered_rows = [
        row for row in failure_rows if selected_reason == "all" or row.get("failure_reason") == selected_reason
    ]

    display_rows = [
        {
            "case_id": row.get("case_id"),
            "query": row.get("query"),
            "method": row.get("method"),
            "failure_reason": row.get("failure_reason"),
            "retrieved_doc_ids": row.get("retrieved_doc_ids"),
            "gold_doc_ids": row.get("gold_doc_ids"),
        }
        for row in filtered_rows
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)


def render_app(st) -> None:
    st.set_page_config(page_title="SupportOps-RAG", layout="wide")
    st.title("SupportOps-RAG")
    st.caption("Local demo for retrieval-augmented support and diagnosis.")

    tab_rag, tab_dashboard, tab_failure = st.tabs(["RAG Demo", "Evaluation Dashboard", "Failure Analysis"])
    with tab_rag:
        _render_demo_tab(st)
    with tab_dashboard:
        _render_dashboard_tab(st)
    with tab_failure:
        _render_failure_tab(st)


def main() -> None:
    import streamlit as st  # type: ignore[import-not-found]

    render_app(st)


if __name__ == "__main__":
    main()

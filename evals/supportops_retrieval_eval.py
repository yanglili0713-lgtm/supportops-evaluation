from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.router import route_question
from evals.supportops_datasets import load_supportops_bench, load_supportops_docs
from rag.dense_retriever import DenseEmbeddingRetriever
from rag.chunker import Chunk, chunk_documents
from rag.ingest import Document
from rag.hybrid_retriever import HybridRetriever
from rag.retriever import BM25Retriever, RetrievalResult


SUPPORTED_METHODS = {"bm25", "dense", "hybrid", "hybrid_reranker", "planner"}
REFUSAL_THRESHOLDS = {
    "bm25": 0.18,
    "dense": 0.16,
    "hybrid": 0.20,
    "hybrid_reranker": 0.24,
    "planner": 0.22,
}


@dataclass(frozen=True)
class SearchBundle:
    chunks: list[Chunk]
    bm25: BM25Retriever
    dense: DenseEmbeddingRetriever
    hybrid: HybridRetriever


def run_supportops_retrieval_eval(
    methods: list[str] | None = None,
    output_dir: str | Path = "runs/eval",
    bench_path: str | Path = "evals/supportops_bench.yaml",
    docs_dir: str | Path = "data/docs",
    chunk_size: int = 512,
    chunk_overlap: int = 80,
    search_top_k: int = 30,
    max_cases: int | None = None,
    method_configs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    methods = methods or ["bm25", "hybrid", "hybrid_reranker", "planner"]
    invalid = sorted(set(methods) - SUPPORTED_METHODS)
    if invalid:
        raise ValueError(f"Unsupported methods: {', '.join(invalid)}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cases = load_supportops_bench(bench_path)
    if max_cases:
        cases = cases[:max_cases]

    bundle = _build_search_bundle(docs_dir=docs_dir, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    all_method_summaries: dict[str, dict[str, Any]] = {}
    trace_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for method in methods:
        method_rows = []
        for case in cases:
            row = _evaluate_case(
                case,
                method,
                bundle,
                search_top_k=search_top_k,
                method_config=(method_configs or {}).get(method, {}),
            )
            method_rows.append(row)
            trace_rows.append(row)
            if row["failure_reason"]:
                failure_rows.append(row)

        all_method_summaries[method] = _summarize_rows(method, method_rows)

    summary_payload = {
        "dataset": "supportops",
        "case_count": len(cases),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "search_top_k": search_top_k,
        "methods": all_method_summaries,
    }

    _write_json(output_path / "retrieval_summary.json", summary_payload)
    _write_csv(output_path / "retrieval_summary.csv", all_method_summaries)
    _write_jsonl(output_path / "trace.jsonl", trace_rows)
    _write_jsonl(output_path / "failure_cases.jsonl", failure_rows)
    return summary_payload


def run_supportops_ablation(
    output_dir: str | Path = "runs/eval",
    bench_path: str | Path = "evals/supportops_bench.yaml",
    docs_dir: str | Path = "data/docs",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    variants: list[dict[str, Any]] = [
        {"name": "bm25_only", "method": "bm25"},
        {"name": "dense_only", "method": "dense"},
        {"name": "hybrid", "method": "hybrid"},
        {"name": "hybrid_no_reranker", "method": "hybrid", "method_configs": {"hybrid": {"rerank": False}}},
        {"name": "hybrid_reranker", "method": "hybrid_reranker"},
        {"name": "planner_rag", "method": "planner"},
        {"name": "planner_no_verifier", "method": "planner", "method_configs": {"planner": {"relax_refusal": True}}},
    ]

    top_k_sweeps = [5, 10, 30]
    chunk_sweeps = [256, 512, 1024]

    rows: list[dict[str, Any]] = []

    for variant in variants:
        for top_k in top_k_sweeps:
            result = run_supportops_retrieval_eval(
                methods=[variant["method"]],
                output_dir=output_path / "_tmp",
                bench_path=bench_path,
                docs_dir=docs_dir,
                chunk_size=512,
                search_top_k=top_k,
                method_configs=variant.get("method_configs"),
            )
            method_name = variant["method"]
            summary = result["methods"][method_name]
            rows.append(
                {
                    "variant": variant["name"],
                    "top_k": top_k,
                    "chunk_size": 512,
                    "method": method_name,
                    **_summary_to_flat_row(summary),
                }
            )

        for chunk_size in chunk_sweeps:
            result = run_supportops_retrieval_eval(
                methods=[variant["method"]],
                output_dir=output_path / "_tmp",
                bench_path=bench_path,
                docs_dir=docs_dir,
                chunk_size=chunk_size,
                search_top_k=10,
                method_configs=variant.get("method_configs"),
            )
            method_name = variant["method"]
            summary = result["methods"][method_name]
            rows.append(
                {
                    "variant": variant["name"],
                    "top_k": 10,
                    "chunk_size": chunk_size,
                    "method": method_name,
                    **_summary_to_flat_row(summary),
                }
            )

    summary_payload = {"dataset": "supportops", "rows": rows}
    _write_json(output_path / "ablation_summary.json", summary_payload)
    _write_csv_rows(output_path / "ablation_summary.csv", rows)
    return summary_payload


def run_supportops_alpha_sweep(
    alphas: list[float],
    output_dir: str | Path = "runs/eval_alpha",
    bench_path: str | Path = "evals/supportops_bench.yaml",
    docs_dir: str | Path = "data/docs",
    chunk_size: int = 512,
    chunk_overlap: int = 80,
    search_top_k: int = 30,
    max_cases: int | None = None,
) -> dict[str, Any]:
    if not alphas:
        raise ValueError("--alpha-sweep must contain at least one value")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cases = load_supportops_bench(bench_path)
    if max_cases:
        cases = cases[:max_cases]

    base_bundle = _build_search_bundle(docs_dir=docs_dir, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    rows: list[dict[str, Any]] = []

    for alpha in alphas:
        hybrid = HybridRetriever(
            base_bundle.chunks,
            alpha=alpha,
            bm25=base_bundle.bm25,
            dense=base_bundle.dense,
        )
        alpha_bundle = SearchBundle(
            chunks=base_bundle.chunks,
            bm25=base_bundle.bm25,
            dense=base_bundle.dense,
            hybrid=hybrid,
        )

        method_rows: list[dict[str, Any]] = []
        for case in cases:
            row = _evaluate_case(
                case,
                "hybrid",
                alpha_bundle,
                search_top_k=search_top_k,
                method_config={"rerank": False},
            )
            method_rows.append(row)

        summary = _summarize_rows("hybrid", method_rows)
        rows.append(
            {
                "alpha": round(float(alpha), 4),
                "method": "hybrid",
                "variant": f"alpha_{alpha}",
                **_summary_to_flat_row(summary),
                **hybrid.backend_info(),
            }
        )

    summary_payload = {
        "dataset": "supportops",
        "case_count": len(cases),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "search_top_k": search_top_k,
        "alphas": [round(float(alpha), 4) for alpha in alphas],
        "rows": rows,
    }

    _write_json(output_path / "alpha_sweep_summary.json", summary_payload)
    _write_csv_rows(output_path / "alpha_sweep_summary.csv", rows)
    _write_json(output_path / "ablation_summary.json", summary_payload)
    _write_csv_rows(output_path / "ablation_summary.csv", rows)
    return summary_payload


def _evaluate_case(
    case: dict[str, Any],
    method: str,
    bundle: SearchBundle,
    search_top_k: int,
    method_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    route_result = route_question(case["query"])
    search_result = _search_case(case, method, bundle, search_top_k=search_top_k, method_config=method_config or {})
    latency_ms = round((time.perf_counter() - started) * 1000, 4)

    retrieved_doc_ids = _unique_doc_ids(search_result["retrieved"])
    gold_doc_ids = case.get("gold_doc_ids", [])
    hit_at_5 = _has_hit(retrieved_doc_ids, gold_doc_ids, 5)
    hit_at_10 = _has_hit(retrieved_doc_ids, gold_doc_ids, 10)
    mrr_at_10 = _mrr_at_k(retrieved_doc_ids, gold_doc_ids, 10)
    ndcg_at_10 = _ndcg_at_k(retrieved_doc_ids, gold_doc_ids, 10)
    top1_precision = _top1_precision(retrieved_doc_ids, gold_doc_ids)
    refusal_decision = _should_refuse(case, search_result, method)
    failure_reason = _failure_reason(
        case=case,
        method=method,
        route_result=route_result,
        retrieved_doc_ids=retrieved_doc_ids,
        refusal_decision=refusal_decision,
        top1_precision=top1_precision,
        top_score=search_result["top_score"],
    )

    return {
        "case_id": case["id"],
        "query": case["query"],
        "method": method,
        "intent": case["intent"],
        "retrieved_doc_ids": retrieved_doc_ids,
        "gold_doc_ids": gold_doc_ids,
        "retrieved_evidence": _format_retrieved_evidence(search_result["retrieved"]),
        "hit_at_5": hit_at_5,
        "hit_at_10": hit_at_10,
        "mrr_at_10": mrr_at_10,
        "ndcg_at_10": ndcg_at_10,
        "top1_evidence_precision": top1_precision,
        "latency_ms": latency_ms,
        "planner_decision": search_result["planner_decision"],
        "refusal_decision": refusal_decision,
        "failure_reason": failure_reason,
        "route_intent": route_result["intent"],
        "route_confidence": route_result["confidence"],
        "top_score": search_result["top_score"],
        "top_k": search_result["top_k"],
        "no_answer": case.get("no_answer", False),
        "requires_multi_doc": case.get("requires_multi_doc", False),
    }


def _search_case(
    case: dict[str, Any],
    method: str,
    bundle: SearchBundle,
    search_top_k: int,
    method_config: dict[str, Any],
) -> dict[str, Any]:
    query = case["query"]
    planner = None
    rerank = method_config.get("rerank", False if method == "hybrid" else True)

    if method == "bm25":
        retrieved = bundle.bm25.search(query, top_k=search_top_k)
        planner = "bm25"
    elif method == "dense":
        retrieved = bundle.dense.search(query, top_k=search_top_k)
        planner = "dense"
    elif method == "hybrid":
        retrieved = bundle.hybrid.search(query, top_k=search_top_k, rerank=rerank)
        planner = "hybrid" if not rerank else "hybrid_reranker"
    elif method == "hybrid_reranker":
        retrieved = bundle.hybrid.search(query, top_k=search_top_k, rerank=True)
        planner = "hybrid_reranker"
    elif method == "planner":
        retrieved, planner = _planner_search(case, bundle, search_top_k=search_top_k, method_config=method_config)
    else:
        raise ValueError(f"Unsupported method: {method}")

    top_score = retrieved[0].score if retrieved else 0.0
    return {
        "retrieved": retrieved,
        "top_score": round(top_score, 4),
        "top_k": len(retrieved),
        "planner_decision": planner,
    }


def _planner_search(
    case: dict[str, Any],
    bundle: SearchBundle,
    search_top_k: int,
    method_config: dict[str, Any],
) -> tuple[list[RetrievalResult], str]:
    route = route_question(case["query"])
    intent = route["intent"]
    if intent in {"api_key_issue", "permission_issue", "rag_upload_issue", "deployment_error"}:
        retrieved = bundle.hybrid.search(case["query"], top_k=search_top_k, rerank=True)
        strategy = "hybrid_reranker"
    elif intent in {"billing_refund", "login_issue", "general_faq"}:
        retrieved = bundle.hybrid.search(case["query"], top_k=search_top_k, rerank=False)
        strategy = "hybrid"
    else:
        retrieved = bundle.bm25.search(case["query"], top_k=search_top_k)
        strategy = "bm25"

    threshold = 0.0 if method_config.get("relax_refusal") else REFUSAL_THRESHOLDS["planner"]
    planner_decision = f"route={intent}; strategy={strategy}; threshold={threshold}"
    return retrieved, planner_decision


def _hybrid_search(
    bundle: SearchBundle,
    query: str,
    top_k: int = 30,
    rerank: bool = True,
) -> list[RetrievalResult]:
    return bundle.hybrid.search(query, top_k=top_k, rerank=rerank)


@lru_cache(maxsize=8)
def _build_search_bundle(
    docs_dir: str | Path,
    chunk_size: int,
    chunk_overlap: int,
) -> SearchBundle:
    docs_raw = load_supportops_docs(docs_dir)
    docs = [
        Document(
            doc_id=item["doc_id"],
            source=item["source"],
            text=item["text"],
        )
        for item in docs_raw
    ]
    chunks = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return SearchBundle(
        chunks=chunks,
        bm25=BM25Retriever(chunks),
        dense=DenseEmbeddingRetriever(chunks),
        hybrid=HybridRetriever(chunks, alpha=0.6),
    )


def _should_refuse(case: dict[str, Any], search_result: dict[str, Any], method: str) -> bool:
    top_score = search_result["top_score"]
    threshold = REFUSAL_THRESHOLDS[method]
    gold_doc_ids = set(case.get("gold_doc_ids", []))
    retrieved_doc_ids = set(_unique_doc_ids(search_result["retrieved"]))
    any_gold_hit = bool(gold_doc_ids & retrieved_doc_ids)
    planner_decision = search_result.get("planner_decision", "")
    if "threshold=0.0" in planner_decision:
        threshold = 0.0

    if case.get("no_answer"):
        return top_score < threshold or not any_gold_hit

    if not any_gold_hit and top_score < threshold:
        return True

    return False


def _failure_reason(
    case: dict[str, Any],
    method: str,
    route_result: dict[str, Any],
    retrieved_doc_ids: list[str],
    refusal_decision: bool,
    top1_precision: float | None,
    top_score: float,
) -> str | None:
    gold_doc_ids = case.get("gold_doc_ids", [])
    top10 = set(retrieved_doc_ids[:10])
    gold = set(gold_doc_ids)

    if gold_doc_ids and not (gold & top10):
        return "missing_gold_evidence"
    if gold_doc_ids and top1_precision == 0.0:
        return "wrong_top1"
    if case.get("no_answer") and not refusal_decision:
        return "should_refuse_but_answered"
    if not case.get("no_answer") and refusal_decision and top_score < REFUSAL_THRESHOLDS[method]:
        return "low_score_refused"
    if not case.get("no_answer") and refusal_decision:
        return "should_answer_but_refused"
    if method == "planner" and route_result["intent"] != case["intent"]:
        return "planner_wrong_route"
    if case.get("requires_multi_doc") and len(gold) > 1 and len(gold & top10) < len(gold) and top10:
        return "evidence_conflict"
    return None


def _summarize_rows(method: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "method": method,
        "case_count": len(rows),
        "applicable_case_count": sum(1 for row in rows if row["gold_doc_ids"]),
        "recall_at_5": _mean(row["hit_at_5"] for row in rows if row["gold_doc_ids"]),
        "recall_at_10": _mean(row["hit_at_10"] for row in rows if row["gold_doc_ids"]),
        "recall_at_30": _mean(_recall_at_30(row) for row in rows if row["gold_doc_ids"]),
        "mrr_at_10": _mean(row["mrr_at_10"] for row in rows if row["gold_doc_ids"]),
        "ndcg_at_10": _mean(row["ndcg_at_10"] for row in rows if row["gold_doc_ids"]),
        "top1_evidence_precision": _mean(row["top1_evidence_precision"] for row in rows if row["gold_doc_ids"]),
        "no_answer_refusal_accuracy": _refusal_accuracy(rows),
        "refusal_f1": _refusal_f1(rows),
        "route_accuracy": _mean(
            1.0 if row["route_intent"] == row["intent"] else 0.0 for row in rows
        ) if method == "planner" else None,
        "latency_ms": _latency_summary([row["latency_ms"] for row in rows]),
    }


def _summary_to_flat_row(summary: dict[str, Any]) -> dict[str, Any]:
    latency = summary["latency_ms"]
    return {
        "case_count": summary["case_count"],
        "applicable_case_count": summary["applicable_case_count"],
        "recall_at_5": summary["recall_at_5"],
        "recall_at_10": summary["recall_at_10"],
        "recall_at_30": summary["recall_at_30"],
        "mrr_at_10": summary["mrr_at_10"],
        "ndcg_at_10": summary["ndcg_at_10"],
        "top1_evidence_precision": summary["top1_evidence_precision"],
        "no_answer_refusal_accuracy": summary["no_answer_refusal_accuracy"],
        "refusal_f1": summary["refusal_f1"],
        "route_accuracy": summary["route_accuracy"],
        "latency_p50_ms": latency["p50"],
        "latency_p95_ms": latency["p95"],
    }


def _format_retrieved_evidence(results: list[RetrievalResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, result in enumerate(results, start=1):
        rows.append(
            {
                "rank": rank,
                "chunk_id": result.chunk_id,
                "doc_id": result.doc_id,
                "score": round(result.score, 4),
                "bm25_score": _optional_score(result.bm25_score),
                "dense_score": _optional_score(result.dense_score),
                "hybrid_score": _optional_score(result.hybrid_score),
                "rerank_score": _optional_score(result.rerank_score),
                "text_snippet": " ".join(result.text.split())[:220],
            }
        )
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_csv(path: Path, summaries: dict[str, dict[str, Any]]) -> None:
    fieldnames = [
        "method",
        "case_count",
        "applicable_case_count",
        "recall_at_5",
        "recall_at_10",
        "recall_at_30",
        "mrr_at_10",
        "ndcg_at_10",
        "top1_evidence_precision",
        "no_answer_refusal_accuracy",
        "refusal_f1",
        "route_accuracy",
        "latency_p50_ms",
        "latency_p95_ms",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries.values():
            writer.writerow({"method": summary["method"], **_summary_to_flat_row(summary)})


def _write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _unique_doc_ids(results: list[RetrievalResult]) -> list[str]:
    ordered: list[str] = []
    for result in results:
        if result.doc_id not in ordered:
            ordered.append(result.doc_id)
    return ordered


def _has_hit(retrieved: list[str], gold: list[str], k: int) -> bool:
    return bool(set(retrieved[:k]) & set(gold))


def _recall_at_30(row: dict[str, Any]) -> float | None:
    return 1.0 if _has_hit(row["retrieved_doc_ids"], row["gold_doc_ids"], 30) else 0.0


def _top1_precision(retrieved: list[str], gold: list[str]) -> float | None:
    if not gold:
        return None
    if not retrieved:
        return 0.0
    return 1.0 if retrieved[0] in set(gold) else 0.0


def _mrr_at_k(retrieved: list[str], gold: list[str], k: int) -> float | None:
    if not gold:
        return None
    gold_set = set(gold)
    for idx, doc_id in enumerate(retrieved[:k], start=1):
        if doc_id in gold_set:
            return round(1.0 / idx, 4)
    return 0.0


def _ndcg_at_k(retrieved: list[str], gold: list[str], k: int) -> float | None:
    if not gold:
        return None
    gold_set = set(gold)

    def dcg(items: list[str]) -> float:
        value = 0.0
        for idx, doc_id in enumerate(items[:k], start=1):
            rel = 1 if doc_id in gold_set else 0
            if rel:
                value += (2**rel - 1) / math.log2(idx + 1)
        return value

    ideal = [doc_id for doc_id in gold[:k]]
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return round(dcg(retrieved) / ideal_dcg, 4)


def _mean(values: Any) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _optional_score(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _latency_summary(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0}
    values = sorted(latencies_ms)
    return {
        "p50": round(_percentile(values, 50), 4),
        "p95": round(_percentile(values, 95), 4),
    }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    rank = (pct / 100) * (len(values) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return values[int(rank)]
    weight = rank - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _refusal_accuracy(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    correct = 0
    for row in rows:
        if bool(row.get("no_answer")) == bool(row.get("refusal_decision")):
            correct += 1
    return round(correct / len(rows), 4)


def _refusal_f1(rows: list[dict[str, Any]]) -> float | None:
    return _refusal_metrics(rows)["f1"]


def _refusal_metrics(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    tp = fp = tn = fn = 0
    for row in rows:
        should_refuse = bool(row.get("no_answer"))
        predicted = bool(row.get("refusal_decision"))
        if should_refuse and predicted:
            tp += 1
        elif should_refuse and not predicted:
            fn += 1
        elif not should_refuse and predicted:
            fp += 1
        else:
            tn += 1
    total = tp + tn + fp + fn
    accuracy = round((tp + tn) / total, 4) if total else None
    precision = round(tp / (tp + fp), 4) if tp + fp else None
    recall = round(tp / (tp + fn), 4) if tp + fn else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = round(2 * precision * recall / (precision + recall), 4)
    return {"accuracy": accuracy, "f1": f1}

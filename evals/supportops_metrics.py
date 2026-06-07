from __future__ import annotations

from typing import Any


ROUTE_METRIC_PIPELINES = {"dummy", "planner"}


def normalize_text(text: str) -> str:
    return (text or "").lower().strip()


def keyword_hit_rate(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0

    answer_norm = normalize_text(answer)
    hits = 0

    for keyword in expected_keywords:
        if normalize_text(keyword) in answer_norm:
            hits += 1

    return hits / len(expected_keywords)


def evidence_recall_at_k(
    retrieved_docs: list[str],
    expected_docs: list[str],
    k: int = 5,
) -> float:
    if not expected_docs:
        return 1.0

    topk = retrieved_docs[:k]
    if not topk:
        return 0.0

    expected = set(expected_docs)
    retrieved = set(topk)

    return len(retrieved & expected) / len(expected)


def evidence_precision_at_k(
    retrieved_docs: list[str],
    expected_docs: list[str],
    k: int = 5,
) -> float | None:
    if not expected_docs:
        return None

    topk = retrieved_docs[:k]
    if not topk:
        return 0.0

    expected = set(expected_docs)
    matched = [doc for doc in topk if doc in expected]

    return len(matched) / len(topk)


def refusal_correct(answer: str, should_refuse: bool) -> bool:
    answer_norm = normalize_text(answer)

    refusal_markers = [
        "不知道",
        "无法确认",
        "没有足够证据",
        "知识库中没有",
        "无法根据现有信息",
        "cannot determine",
        "not enough evidence",
        "i don't know",
        "i do not know",
        "not found",
        "cannot answer",
    ]

    refused = any(marker in answer_norm for marker in refusal_markers)

    return refused == should_refuse


def route_correct(predicted_route: str | None, expected_route: str | None) -> float | None:
    if not expected_route:
        return None

    if not predicted_route:
        return 0.0

    return 1.0 if predicted_route == expected_route else 0.0


def latency_summary(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {
            "avg": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "max": 0.0,
        }

    values = sorted(latencies_ms)
    n = len(values)

    def percentile(p: float) -> float:
        if n == 1:
            return values[0]

        idx = int(round((p / 100) * (n - 1)))
        idx = max(0, min(idx, n - 1))
        return values[idx]

    return {
        "avg": round(sum(values) / n, 4),
        "p50": round(percentile(50), 4),
        "p95": round(percentile(95), 4),
        "max": round(max(values), 4),
    }


def _mean(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None

    return round(sum(valid) / len(valid), 4)


def score_case(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    answer = prediction.get("answer", "")
    retrieved_docs = prediction.get("retrieved_docs", [])
    predicted_route = prediction.get("route")

    expected_docs = case.get("expected_docs", [])
    expected_keywords = case.get("expected_keywords", [])
    expected_route = case.get("expected_route")

    return {
        "id": case["id"],
        "task_type": case.get("task_type", ""),
        "split": case.get("split", ""),
        "difficulty": case.get("difficulty", ""),
        "keyword_hit_rate": keyword_hit_rate(answer, expected_keywords),
        "evidence_recall_at_5": evidence_recall_at_k(retrieved_docs, expected_docs, k=5),
        "evidence_precision_at_5": evidence_precision_at_k(retrieved_docs, expected_docs, k=5),
        "refusal_accuracy": 1.0 if refusal_correct(answer, case.get("should_refuse", False)) else 0.0,
        "route_accuracy": route_correct(predicted_route, expected_route),
    }


def aggregate(scores: list[dict[str, Any]], pipeline_name: str | None = None) -> dict[str, Any]:
    if not scores:
        return {
            "cases": 0,
            "avg_keyword_hit_rate": 0.0,
            "avg_evidence_recall_at_5": 0.0,
            "avg_evidence_precision_at_5": None,
            "avg_refusal_accuracy": 0.0,
            "avg_route_accuracy": None,
            "latency_ms": latency_summary([]),
        }

    if pipeline_name in ROUTE_METRIC_PIPELINES:
        route_scores = [score.get("route_accuracy") for score in scores]
    else:
        route_scores = []

    return {
        "cases": len(scores),
        "avg_keyword_hit_rate": _mean([score["keyword_hit_rate"] for score in scores]),
        "avg_evidence_recall_at_5": _mean([score["evidence_recall_at_5"] for score in scores]),
        "avg_evidence_precision_at_5": _mean([score.get("evidence_precision_at_5") for score in scores]),
        "avg_refusal_accuracy": _mean([score["refusal_accuracy"] for score in scores]),
        "avg_route_accuracy": _mean(route_scores),
        "latency_ms": latency_summary([score.get("latency_ms", 0.0) for score in scores]),
    }

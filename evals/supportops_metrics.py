from __future__ import annotations

import math
import re


REFUSAL_MARKERS = [
    "不知道",
    "无法确认",
    "没有足够证据",
    "知识库中没有",
    "cannot determine",
    "not enough evidence",
    "i don't know",
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def keyword_hit_rate(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    normalized_answer = normalize_text(answer)
    hits = 0
    for keyword in expected_keywords:
        if normalize_text(keyword) in normalized_answer:
            hits += 1
    return hits / len(expected_keywords)


def evidence_recall_at_k(retrieved_docs: list[str], expected_docs: list[str], k: int = 5) -> float:
    if not expected_docs:
        return 1.0
    top_docs = set(retrieved_docs[:k])
    expected = set(expected_docs)
    return len(top_docs & expected) / len(expected)


def refusal_correct(answer: str, should_refuse: bool) -> bool:
    normalized_answer = normalize_text(answer)
    refused = any(marker in normalized_answer for marker in REFUSAL_MARKERS)
    return refused if should_refuse else not refused


def route_correct(predicted_route: str | None, expected_route: str | None) -> float | None:
    if expected_route is None:
        return None
    return 1.0 if predicted_route == expected_route else 0.0


def latency_summary(latencies_ms: list[float]) -> dict:
    if not latencies_ms:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}

    values = sorted(latencies_ms)
    return {
        "avg": round(sum(values) / len(values), 4),
        "p50": round(_percentile(values, 50), 4),
        "p95": round(_percentile(values, 95), 4),
        "max": round(max(values), 4),
    }


def score_case(case: dict, prediction: dict) -> dict:
    expected_docs = case.get("expected_docs", [])
    expected_route = case.get("expected_route")
    answer = prediction.get("answer", "")
    retrieved_docs = prediction.get("retrieved_docs", [])
    route = prediction.get("route")

    return {
        "case_id": case.get("id"),
        "keyword_hit_rate": keyword_hit_rate(answer, case.get("expected_keywords", [])),
        "evidence_recall_at_5": evidence_recall_at_k(retrieved_docs, expected_docs, k=5),
        "refusal_correct": refusal_correct(answer, bool(case.get("should_refuse", False))),
        "route_correct": route_correct(route, expected_route),
        "latency_ms": prediction.get("latency_ms", 0.0),
    }


def aggregate(scores: list[dict]) -> dict:
    route_scores = [score["route_correct"] for score in scores if score.get("route_correct") is not None]
    return {
        "cases": len(scores),
        "avg_keyword_hit_rate": _avg([score.get("keyword_hit_rate", 0.0) for score in scores]),
        "avg_evidence_recall_at_5": _avg([score.get("evidence_recall_at_5", 0.0) for score in scores]),
        "avg_refusal_accuracy": _avg([1.0 if score.get("refusal_correct") else 0.0 for score in scores]),
        "avg_route_accuracy": _avg(route_scores) if route_scores else None,
        "latency_ms": latency_summary([float(score.get("latency_ms", 0.0)) for score in scores]),
    }


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _percentile(values: list[float], percentile: int) -> float:
    if len(values) == 1:
        return values[0]
    rank = (len(values) - 1) * percentile / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return values[int(rank)]
    weight = rank - lower
    return values[lower] * (1 - weight) + values[upper] * weight

from __future__ import annotations

from app.router import route_question
from evals.common import load_gold_cases


def run_eval() -> dict:
    cases = load_gold_cases()
    confusion_matrix: dict[str, dict[str, int]] = {}
    high_confidence_wrong_route = []

    for case in cases:
        router_result = route_question(case["query"])
        expected = case["expected_intent"]
        predicted = router_result["intent"]
        confusion_matrix.setdefault(expected, {})
        confusion_matrix[expected][predicted] = confusion_matrix[expected].get(predicted, 0) + 1

        if predicted != expected and router_result["confidence"] >= 0.8:
            high_confidence_wrong_route.append(
                {
                    "query": case["query"],
                    "expected_intent": expected,
                    "predicted_intent": predicted,
                    "confidence": router_result["confidence"],
                    "reason": router_result["reason"],
                    "matched_keywords": router_result["matched_keywords"],
                }
            )

    return {
        "name": "router_confusion_eval",
        "total_cases": len(cases),
        "confusion_matrix": confusion_matrix,
        "high_confidence_wrong_route": high_confidence_wrong_route,
    }


if __name__ == "__main__":
    print(run_eval())

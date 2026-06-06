from __future__ import annotations

from app.router import route_question
from evals.common import load_gold_cases


def run_eval() -> dict:
    cases = load_gold_cases()
    failed_cases = []

    for case in cases:
        router_result = route_question(case["query"])
        predicted = router_result["intent"]
        expected = case["expected_intent"]
        if predicted != expected:
            failed_cases.append(
                {
                    "query": case["query"],
                    "expected_intent": expected,
                    "predicted_intent": predicted,
                    "confidence": router_result["confidence"],
                    "reason": router_result["reason"],
                }
            )

    accuracy = (len(cases) - len(failed_cases)) / len(cases) if cases else 0.0
    return {
        "name": "tool_recall_eval",
        "total_cases": len(cases),
        "accuracy": round(accuracy, 4),
        "failed_cases": failed_cases,
    }


if __name__ == "__main__":
    print(run_eval())

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evals.supportops_datasets import load_banking77
from evals.text_models import SparseMulticlassLogisticRegression


RULE_ALIASES = {
    "activate_my_card": ["activate card", "card activation", "activate"],
    "apple_pay_or_google_pay": ["apple pay", "google pay", "wallet"],
    "atm_support": ["atm", "cash machine", "cash withdrawal"],
    "automatic_top_up": ["auto top up", "automatic top up", "auto reload"],
    "balance_not_updated_after_bank_transfer": ["balance", "bank transfer", "not updated"],
    "cash_withdrawal_charge": ["cash withdrawal charge", "atm fee", "withdrawal fee"],
    "cash_withdrawal_not_recognised": ["cash withdrawal not recognised", "unauthorized withdrawal"],
    "change_pin": ["change pin", "reset pin", "new pin"],
    "card_arrival": ["card arrival", "delivery", "arrive"],
    "card_not_working": ["card not working", "card failed", "card broken"],
    "cancel_transfer": ["cancel transfer", "stop transfer"],
    "passcode_forgotten": ["passcode forgotten", "forgot passcode", "reset passcode"],
    "request_refund": ["request refund", "refund", "money back"],
    "top_up_failed": ["top up failed", "recharge failed", "deposit failed"],
    "transfer_not_received_by_recipient": ["transfer not received", "recipient not received"],
    "verify_my_identity": ["verify identity", "identity verification"],
}


@dataclass(frozen=True)
class Banking77Prediction:
    label: str
    confidence: float
    method: str


def run_banking77_router_eval(
    output_path: str | Path = "runs/eval/banking77_router_report.json",
    confusion_path: str | Path | None = None,
    split: str = "test",
    max_samples: int | None = 1000,
    train_max_samples: int | None = None,
    sample_path: str | Path | None = None,
    allow_fallback: bool = True,
) -> dict[str, Any]:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    confusion_path = Path(confusion_path) if confusion_path else output_path.with_name("banking77_confusion_cases.jsonl")
    confusion_path.parent.mkdir(parents=True, exist_ok=True)

    train_rows = load_banking77(
        split="train",
        max_samples=train_max_samples,
        sample_path=sample_path,
        allow_fallback=allow_fallback,
    )
    test_rows = load_banking77(
        split=split,
        max_samples=max_samples,
        sample_path=sample_path,
        allow_fallback=allow_fallback,
    )

    labels = sorted({row["intent"] for row in train_rows + test_rows})

    logistic = SparseMulticlassLogisticRegression(max_features=4000, epochs=6, learning_rate=0.35)
    logistic.fit([row["query"] for row in train_rows], [row["intent"] for row in train_rows])

    predictions = {
        "rule": [_predict_rule(row["query"], labels) for row in test_rows],
        "tfidf_lr": [
            _predict_logistic(row["query"], logistic) for row in test_rows
        ],
    }

    method_reports: dict[str, Any] = {}
    confusion_rows: list[dict[str, Any]] = []
    for method, method_predictions in predictions.items():
        report, misclassified = _evaluate_predictions(test_rows, method_predictions, method)
        method_reports[method] = report
        confusion_rows.extend(misclassified)

    payload = {
        "dataset": "banking77",
        "split": split,
        "train_size": len(train_rows),
        "test_size": len(test_rows),
        "methods": method_reports,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_jsonl(confusion_path, confusion_rows)
    return payload


def _predict_rule(query: str, labels: list[str]) -> Banking77Prediction:
    query_norm = _normalize(query)
    best_label = labels[0] if labels else ""
    best_score = -1.0

    for label in labels:
        score = 0.0
        phrase = label.replace("_", " ")
        if phrase in query_norm:
            score += 4.0
        for token in phrase.split():
            if token and token in query_norm:
                score += 1.0
        for alias in RULE_ALIASES.get(label, []):
            alias_norm = alias.lower()
            if alias_norm in query_norm:
                score += 2.5
        if score > best_score:
            best_label = label
            best_score = score

    confidence = 0.0 if best_score <= 0 else round(min(0.99, best_score / (best_score + 3.0)), 4)
    return Banking77Prediction(label=best_label, confidence=confidence, method="rule")


def _predict_logistic(query: str, model: SparseMulticlassLogisticRegression) -> Banking77Prediction:
    result = model.predict_one(query)
    return Banking77Prediction(label=result.label, confidence=0.0, method="tfidf_lr")


def _evaluate_predictions(
    rows: list[dict[str, Any]],
    predictions: list[Banking77Prediction],
    method: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if len(rows) != len(predictions):
        raise ValueError("rows and predictions must have the same length")

    labels = sorted({row["intent"] for row in rows})
    gold_by_label: dict[str, list[int]] = defaultdict(list)
    pred_by_label: dict[str, list[int]] = defaultdict(list)
    correct = 0
    misclassified = []

    for idx, (row, pred) in enumerate(zip(rows, predictions)):
        gold = row["intent"]
        predicted = pred.label
        gold_by_label[gold].append(1)
        pred_by_label[predicted].append(1)
        if gold == predicted:
            correct += 1
        else:
            misclassified.append(
                {
                    "case_id": row["id"],
                    "query": row["query"],
                    "method": method,
                    "gold_intent": gold,
                    "predicted_intent": predicted,
                    "confidence": pred.confidence,
                    "error_type": "intent_mismatch",
                }
            )

    per_class = {}
    f1_scores = []
    for label in labels:
        tp = sum(1 for row, pred in zip(rows, predictions) if row["intent"] == label and pred.label == label)
        fp = sum(1 for row, pred in zip(rows, predictions) if row["intent"] != label and pred.label == label)
        fn = sum(1 for row, pred in zip(rows, predictions) if row["intent"] == label and pred.label != label)
        support = sum(1 for row in rows if row["intent"] == label)
        precision = round(tp / (tp + fp), 4) if tp + fp else 0.0
        recall = round(tp / (tp + fn), 4) if tp + fn else 0.0
        if precision + recall:
            f1 = round(2 * precision * recall / (precision + recall), 4)
        else:
            f1 = 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        f1_scores.append(f1)

    total = len(rows) or 1
    accuracy = round(correct / total, 4)
    macro_f1 = round(sum(f1_scores) / len(f1_scores), 4) if f1_scores else 0.0
    return (
        {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "per_class_report": per_class,
            "confusion_count": len(misclassified),
        },
        misclassified,
    )


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

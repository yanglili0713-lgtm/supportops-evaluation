from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rag.ingest import load_markdown_docs
from evals.supportops_run_eval import load_bench as load_raw_supportops_bench


SUPPORTOPS_DOC_TITLES = {
    "api_key_guide": "API Key Recovery Guide",
    "api_key_token_edge_cases": "API Key and Token Edge Cases",
    "error_code_manual": "Error Code Manual",
    "permission_guide": "Permission Guide",
    "permission_edge_cases": "Permission Edge Cases",
    "rag_upload_troubleshooting": "RAG Upload Troubleshooting",
    "rag_upload_edge_cases": "RAG Upload Edge Cases",
    "refund_policy": "Refund Policy",
    "refund_edge_cases": "Refund Edge Cases",
}

SUPPORTOPS_DOC_TAGS = {
    "api_key_guide": ["api_key", "credential", "token"],
    "api_key_token_edge_cases": ["api_key", "token", "credential"],
    "error_code_manual": ["error_code", "incident", "diagnosis"],
    "permission_guide": ["permission", "access_control"],
    "permission_edge_cases": ["permission", "access_control"],
    "rag_upload_troubleshooting": ["rag", "upload", "embedding"],
    "rag_upload_edge_cases": ["rag", "upload", "embedding"],
    "refund_policy": ["billing", "refund"],
    "refund_edge_cases": ["billing", "refund"],
}

SUPPORTOPS_INTENT_TAGS = {
    "api_key_issue": ["api_key", "credential"],
    "login_issue": ["login"],
    "billing_refund": ["billing", "refund"],
    "rag_upload_issue": ["rag", "upload"],
    "permission_issue": ["permission"],
    "deployment_error": ["incident", "error_code"],
    "general_faq": ["faq"],
    "unknown": ["unknown"],
}

SUPPORTOPS_INTENT_ANSWERS = {
    "api_key_issue": "Check API key status, environment, package scope, and whether the key was deleted or expired.",
    "login_issue": "Check session state, password reset flow, and verification code delivery.",
    "billing_refund": "Review refund eligibility, payment status, invoice state, and manual review constraints.",
    "rag_upload_issue": "Check parsing, chunking, OCR, embedding, and vector index writes.",
    "permission_issue": "Check role assignment, project membership, and access scope.",
    "deployment_error": "Check the error code manual, service logs, timeout conditions, and retry path.",
    "general_faq": "Refer to the knowledge base for the closest documented policy or FAQ.",
    "unknown": "No reliable answer is available from the current knowledge base.",
}

SUPPORTOPS_SAMPLE_BANKING77 = Path("data/banking77_sample.jsonl")


def load_supportops_docs(docs_dir: str | Path = "data/docs") -> list[dict[str, Any]]:
    docs = load_markdown_docs(docs_dir)
    items: list[dict[str, Any]] = []
    for doc in docs:
        title = SUPPORTOPS_DOC_TITLES.get(doc.doc_id, doc.doc_id.replace("_", " ").title())
        items.append(
            {
                "doc_id": doc.doc_id,
                "title": title,
                "text": doc.text,
                "source": "supportops_seed",
                "tags": SUPPORTOPS_DOC_TAGS.get(doc.doc_id, [doc.doc_id]),
            }
        )
    return items


def load_supportops_bench(path: str | Path = "evals/supportops_bench.yaml") -> list[dict[str, Any]]:
    raw_cases = load_raw_supportops_bench(path)
    normalized: list[dict[str, Any]] = []
    for case in raw_cases:
        normalized.append(_normalize_supportops_case(case))
    return normalized


def _normalize_supportops_case(case: dict[str, Any]) -> dict[str, Any]:
    gold_doc_ids = [Path(doc).stem for doc in case.get("expected_docs", [])]
    intent = case.get("intent") or case.get("expected_route") or _intent_from_task_type(case.get("task_type", ""))
    no_answer = bool(case.get("should_refuse")) or case.get("task_type") in {"no_answer", "security_boundary"}
    tags = sorted(
        {
            *SUPPORTOPS_INTENT_TAGS.get(intent, [intent]),
            *case.get("task_type", "").split("_"),
            *sum((SUPPORTOPS_DOC_TAGS.get(doc_id, []) for doc_id in gold_doc_ids), []),
        }
    )
    return {
        "id": case["id"],
        "query": case["query"],
        "intent": intent,
        "difficulty": case.get("difficulty", "medium"),
        "gold_doc_ids": gold_doc_ids,
        "gold_answer": _gold_answer(intent, gold_doc_ids, case.get("expected_keywords", []), no_answer),
        "no_answer": no_answer,
        "requires_multi_doc": bool(case.get("requires_multi_doc")),
        "tags": tags,
        "task_type": case.get("task_type", ""),
        "split": case.get("split", ""),
        "expected_keywords": case.get("expected_keywords", []),
        "should_refuse": bool(case.get("should_refuse")),
        "expected_route": case.get("expected_route", intent),
    }


def _intent_from_task_type(task_type: str) -> str:
    mapping = {
        "faq": "general_faq",
        "api_key_recovery": "api_key_issue",
        "credential_or_token": "api_key_issue",
        "permission_issue": "permission_issue",
        "incident_diagnosis": "deployment_error",
        "rag_upload_issue": "rag_upload_issue",
        "refund_policy": "billing_refund",
        "login_issue": "login_issue",
        "multi_doc_diagnosis": "deployment_error",
        "no_answer": "unknown",
        "security_boundary": "unknown",
    }
    return mapping.get(task_type, "unknown")


def _gold_answer(intent: str, gold_doc_ids: list[str], expected_keywords: list[str], no_answer: bool) -> str:
    if no_answer:
        return "No answer should be given; escalate or ask for more information."
    base = SUPPORTOPS_INTENT_ANSWERS.get(intent, SUPPORTOPS_INTENT_ANSWERS["unknown"])
    if gold_doc_ids:
        docs = ", ".join(gold_doc_ids)
        return f"{base} Evidence should come from: {docs}."
    if expected_keywords:
        keywords = ", ".join(expected_keywords[:4])
        return f"{base} Key signals: {keywords}."
    return base


def load_banking77(
    split: str = "test",
    max_samples: int | None = None,
    sample_path: str | Path | None = None,
    allow_download: bool = True,
    allow_fallback: bool = True,
) -> list[dict[str, Any]]:
    if sample_path:
        return _load_banking77_sample(sample_path, max_samples=max_samples)

    if allow_download:
        try:
            from datasets import load_dataset  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            if allow_fallback:
                return _load_banking77_sample(SUPPORTOPS_SAMPLE_BANKING77, max_samples=max_samples)
            raise RuntimeError(
                "datasets is not installed; provide --sample-path or enable fallback"
            ) from exc

        try:
            dataset = load_dataset("PolyAI/banking77", split=split)
        except Exception as exc:  # noqa: BLE001
            if allow_fallback:
                return _load_banking77_sample(SUPPORTOPS_SAMPLE_BANKING77, max_samples=max_samples)
            raise RuntimeError(
                f"Unable to load BANKING77 split={split}; provide a sample fixture or retry with network access"
            ) from exc

        items: list[dict[str, Any]] = []
        label_names = None
        try:
            label_names = list(dataset.features["label"].names)  # type: ignore[index]
        except Exception:  # noqa: BLE001
            label_names = None

        for idx, row in enumerate(dataset):
            label = row.get("label")
            intent = label_names[label] if isinstance(label, int) and label_names else str(label)
            items.append(
                {
                    "id": f"banking77_{split}_{idx:05d}",
                    "query": row["text"],
                    "intent": intent,
                    "label": intent,
                    "split": split,
                    "source": "hf:PolyAI/banking77",
                }
            )
            if max_samples and len(items) >= max_samples:
                break
        return items

    if allow_fallback:
        return _load_banking77_sample(SUPPORTOPS_SAMPLE_BANKING77, max_samples=max_samples)

    raise RuntimeError("BANKING77 download disabled and no sample fallback configured")


def _load_banking77_sample(path: str | Path, max_samples: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        record = {
            "id": record.get("id") or f"sample_{len(rows):05d}",
            "query": record["query"],
            "intent": record["intent"],
            "label": record.get("label", record["intent"]),
            "split": record.get("split", "sample"),
            "source": record.get("source", "sample_fixture"),
        }
        rows.append(record)
        if max_samples and len(rows) >= max_samples:
            break
    return rows

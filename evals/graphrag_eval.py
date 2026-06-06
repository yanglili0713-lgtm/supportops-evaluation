from __future__ import annotations

from graph.entity_linker import link_entities
from graph.graph_retriever import GraphRetriever


def run_eval() -> dict:
    retriever = GraphRetriever()
    user_evidence = retriever.retrieve(link_entities("user_id 是 u_1001"))
    error_evidence = retriever.retrieve(link_entities("错误码 EMBEDDING_FAILED"))

    checks = {
        "u_1001_has_project": _contains_label(user_evidence, "Project"),
        "u_1001_has_upload_job": _contains_label(user_evidence, "UploadJob"),
        "embedding_failed_has_service": _contains_label(error_evidence, "Service"),
        "embedding_failed_has_ticket": _contains_label(error_evidence, "Ticket"),
        "evidence_has_paths": all("path" in item and "relationships" in item for item in user_evidence + error_evidence),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    return {
        "name": "graphrag_eval",
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": {
            "user_evidence": user_evidence,
            "error_evidence": error_evidence,
        },
    }


def _contains_label(evidence: list[dict], label: str) -> bool:
    return any(node["label"] == label for item in evidence for node in item["path"])


if __name__ == "__main__":
    print(run_eval())

from __future__ import annotations

from app.memory import CaseState


def plan_retrieval(
    user_message: str,
    case_state: CaseState,
    router_result: dict,
    selected_skill: dict,
) -> dict:
    intent = router_result.get("intent")
    steps = ["bm25_rag", "vector_rag"]

    if intent in {"rag_upload_issue", "api_key_issue", "permission_issue", "deployment_error"}:
        steps.append("graph_rag")
    if case_state.error_code or intent in {"rag_upload_issue", "api_key_issue", "deployment_error"}:
        steps.append("logs_tool")
    if intent == "billing_refund":
        steps.append("billing_tool")
    if selected_skill.get("skill_name") == "escalation":
        steps.append("ticket_tool")
    if intent == "unknown":
        steps.append("escalate")

    return {
        "steps": steps,
        "reason": f"planned evidence for intent={intent}, skill={selected_skill.get('skill_name')}",
        "max_retries": 2,
    }

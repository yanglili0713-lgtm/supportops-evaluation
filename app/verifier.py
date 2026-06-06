from __future__ import annotations


def evidence_sufficiency_check(evidence: dict) -> dict:
    missing = []
    warnings = []

    if not evidence.get("citations"):
        missing.append("citations")
    if evidence.get("needs_graph") and not evidence.get("graph_evidence"):
        missing.append("graph_evidence")
    if evidence.get("needs_tool") and not evidence.get("tool_calls"):
        missing.append("tool_calls")

    for tool_call in evidence.get("tool_calls", []):
        result = tool_call.get("result", {})
        if not result.get("ok", False):
            warnings.append(f"tool failed: {tool_call.get('tool_name')}")
        if result.get("dry_run") is False and tool_call.get("is_write"):
            warnings.append(f"write tool was not dry_run: {tool_call.get('tool_name')}")

    if missing:
        next_action = "retry_retrieval"
    elif warnings:
        next_action = "review_warnings"
    else:
        next_action = "answer"

    return {
        "sufficient": not missing,
        "missing_evidence": missing,
        "warnings": warnings,
        "next_action": next_action,
    }

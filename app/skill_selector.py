from __future__ import annotations


INTENT_TO_SKILL = {
    "billing_refund": "refund_policy",
    "login_issue": "login_troubleshooting",
    "api_key_issue": "api_key_recovery",
    "rag_upload_issue": "rag_upload_debug",
    "unknown": "escalation",
}

TODO_ESCALATION_INTENTS = {"permission_issue", "deployment_error"}


def select_skill(router_intent: str | None) -> dict:
    if router_intent in INTENT_TO_SKILL:
        skill_name = INTENT_TO_SKILL[router_intent]
        return {
            "skill_name": skill_name,
            "reason": f"router intent {router_intent} maps to {skill_name}",
            "confidence": 0.9 if router_intent != "unknown" else 0.6,
        }

    if router_intent in TODO_ESCALATION_INTENTS:
        return {
            "skill_name": "escalation",
            "reason": (
                f"router intent {router_intent} is recognized, but its dedicated "
                "skill is TODO for this phase"
            ),
            "confidence": 0.55,
        }

    return {
        "skill_name": "escalation",
        "reason": "router intent is missing or unsupported",
        "confidence": 0.4,
    }

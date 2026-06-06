from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


SUPPORTED_PLANS = {"free", "pro", "enterprise"}

ERROR_CODE_RE = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")
INVOICE_ID_RE = re.compile(r"\binv_[0-9]+\b", re.IGNORECASE)
USER_ID_RE = re.compile(r"\bu_[0-9]+\b", re.IGNORECASE)

FILE_TYPE_PATTERNS = {
    "PDF": ("pdf",),
    "docx": ("docx", ".docx"),
    "txt": ("txt", ".txt"),
}

ATTEMPTED_STEP_PATTERNS = {
    "重新上传过": ("重新上传过", "重新上传", "上传过"),
    "重新登录过": ("重新登录过", "重新登录", "登出再登录", "退出再登录"),
    "换过 API Key": ("换过 api key", "更换过 api key", "换了 api key", "换过apikey"),
}


@dataclass
class CaseState:
    user_id: str | None = None
    plan: str | None = None
    intent: str | None = None
    error_code: str | None = None
    invoice_id: str | None = None
    uploaded_file_type: str | None = None
    attempted_steps: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)
    last_router_intent: str | None = None
    current_decision: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def update_case_state(
    state: CaseState,
    user_message: str,
    router_result: Any | None = None,
) -> CaseState:
    """Merge one user turn into the structured case state."""
    text = user_message.strip()
    lower_text = text.lower()

    router_intent = _get_router_intent(router_result)
    if router_intent:
        state.last_router_intent = router_intent
        state.intent = router_intent

    if user_id := _extract_user_id(text):
        state.user_id = user_id
    if plan := _extract_plan(lower_text):
        state.plan = plan
    if error_code := _extract_error_code(text):
        state.error_code = error_code
    if invoice_id := _extract_invoice_id(text):
        state.invoice_id = invoice_id
    if file_type := _extract_file_type(lower_text):
        state.uploaded_file_type = file_type

    for attempted_step in _extract_attempted_steps(lower_text):
        if attempted_step not in state.attempted_steps:
            state.attempted_steps.append(attempted_step)

    state.missing_info = _build_missing_info(state)
    state.current_decision = "need_more_info" if state.missing_info else "ready_for_next_step"
    return state


def _get_router_intent(router_result: Any | None) -> str | None:
    if router_result is None:
        return None
    if isinstance(router_result, dict):
        return router_result.get("intent")
    return getattr(router_result, "intent", None)


def _extract_user_id(text: str) -> str | None:
    match = USER_ID_RE.search(text)
    return match.group(0).lower() if match else None


def _extract_plan(lower_text: str) -> str | None:
    for plan in SUPPORTED_PLANS:
        if re.search(rf"\b{plan}\b", lower_text):
            return plan
    return None


def _extract_error_code(text: str) -> str | None:
    match = ERROR_CODE_RE.search(text)
    return match.group(0) if match else None


def _extract_invoice_id(text: str) -> str | None:
    match = INVOICE_ID_RE.search(text)
    return match.group(0).lower() if match else None


def _extract_file_type(lower_text: str) -> str | None:
    for file_type, patterns in FILE_TYPE_PATTERNS.items():
        if any(pattern in lower_text for pattern in patterns):
            return file_type
    return None


def _extract_attempted_steps(lower_text: str) -> list[str]:
    steps: list[str] = []
    compact_text = lower_text.replace(" ", "")
    for step, patterns in ATTEMPTED_STEP_PATTERNS.items():
        for pattern in patterns:
            compact_pattern = pattern.replace(" ", "")
            if pattern in lower_text or compact_pattern in compact_text:
                steps.append(step)
                break
    return steps


def _build_missing_info(state: CaseState) -> list[str]:
    missing = []
    if not state.user_id:
        missing.append("user_id")
    if state.intent == "billing_refund" and not state.invoice_id:
        missing.append("invoice_id")
    if state.intent == "rag_upload_issue" and not state.uploaded_file_type:
        missing.append("uploaded_file_type")
    return missing

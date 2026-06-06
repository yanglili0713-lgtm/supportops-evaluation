from __future__ import annotations

import re
from typing import Any


USER_ID_RE = re.compile(r"\bu_[0-9]+\b", re.IGNORECASE)
ERROR_CODE_RE = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")
SERVICE_RE = re.compile(r"\b[a-z]+_service\b")
TICKET_ID_RE = re.compile(r"\bticket_[0-9]+\b", re.IGNORECASE)
PROJECT_ID_RE = re.compile(r"\bproj_[a-z0-9_]+\b", re.IGNORECASE)


def link_entities(text: str = "", case_state: dict[str, Any] | None = None) -> dict[str, str]:
    case_state = case_state or {}
    entities: dict[str, str] = {}

    if user_id := case_state.get("user_id"):
        entities["user_id"] = user_id
    if error_code := case_state.get("error_code"):
        entities["error_code"] = error_code

    _match_into(entities, "user_id", USER_ID_RE, text.lower())
    _match_into(entities, "error_code", ERROR_CODE_RE, text)
    _match_into(entities, "service", SERVICE_RE, text.lower())
    _match_into(entities, "ticket_id", TICKET_ID_RE, text.lower())
    _match_into(entities, "project_id", PROJECT_ID_RE, text.lower())
    return entities


def _match_into(entities: dict[str, str], key: str, pattern: re.Pattern, text: str) -> None:
    if key in entities:
        return
    match = pattern.search(text)
    if match:
        entities[key] = match.group(0)

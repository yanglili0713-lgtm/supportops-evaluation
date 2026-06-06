from __future__ import annotations

from typing import Any

from mcp_servers.common import load_mock_json, tool_result


def search_error_logs(
    user_id: str | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    if not user_id and not error_code:
        return tool_result(
            ok=False,
            action="search_error_logs",
            error="user_id or error_code is required",
        )

    logs = load_mock_json("logs.json")
    matched = []
    for log in logs:
        if user_id and log["user_id"] != user_id:
            continue
        if error_code and log["error_code"] != error_code:
            continue
        matched.append(log)

    return tool_result(ok=True, action="search_error_logs", data=matched)

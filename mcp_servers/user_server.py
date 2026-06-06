from __future__ import annotations

from typing import Any

from mcp_servers.common import load_mock_json, tool_result


def get_user_profile(user_id: str) -> dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        return tool_result(
            ok=False,
            action="get_user_profile",
            error=f"user not found: {user_id}",
        )
    return tool_result(ok=True, action="get_user_profile", data=user)


def get_user_plan(user_id: str) -> dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        return tool_result(
            ok=False,
            action="get_user_plan",
            error=f"user not found: {user_id}",
        )
    return tool_result(
        ok=True,
        action="get_user_plan",
        data={"user_id": user["user_id"], "plan": user["plan"]},
    )


def get_user_permissions(user_id: str) -> dict[str, Any]:
    user = _find_user(user_id)
    if not user:
        return tool_result(
            ok=False,
            action="get_user_permissions",
            error=f"user not found: {user_id}",
        )

    permissions = _permissions_for_role(user["role"])
    return tool_result(
        ok=True,
        action="get_user_permissions",
        data={
            "user_id": user["user_id"],
            "role": user["role"],
            "team_id": user["team_id"],
            "permissions": permissions,
        },
    )


def _find_user(user_id: str) -> dict[str, Any] | None:
    for user in load_mock_json("users.json"):
        if user["user_id"] == user_id:
            return user
    return None


def _permissions_for_role(role: str) -> list[str]:
    if role == "admin":
        return ["read_project", "manage_team", "view_billing", "create_ticket"]
    return ["read_project", "create_ticket"]

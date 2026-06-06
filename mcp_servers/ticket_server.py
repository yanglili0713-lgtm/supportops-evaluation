from __future__ import annotations

from typing import Any

from mcp_servers.common import tool_result
from mcp_servers.user_server import get_user_profile


_TICKETS: list[dict[str, Any]] = []


def create_ticket(
    user_id: str,
    issue_type: str,
    summary: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    if not get_user_profile(user_id)["ok"]:
        return tool_result(
            ok=False,
            action="create_ticket",
            error=f"user not found: {user_id}",
            dry_run=dry_run,
        )

    ticket = {
        "user_id": user_id,
        "issue_type": issue_type,
        "summary": summary,
        "status": "proposed" if dry_run else "open",
    }
    if not dry_run:
        ticket["ticket_id"] = f"ticket_{len(_TICKETS) + 1:04d}"
        _TICKETS.append(ticket)

    return tool_result(
        ok=True,
        action="create_ticket",
        data=ticket,
        dry_run=dry_run,
    )


def search_tickets(user_id: str) -> dict[str, Any]:
    if not get_user_profile(user_id)["ok"]:
        return tool_result(
            ok=False,
            action="search_tickets",
            error=f"user not found: {user_id}",
        )

    tickets = [ticket for ticket in _TICKETS if ticket["user_id"] == user_id]
    return tool_result(
        ok=True,
        action="search_tickets",
        data={"user_id": user_id, "tickets": tickets},
    )

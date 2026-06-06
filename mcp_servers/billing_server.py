from __future__ import annotations

from typing import Any

from mcp_servers.common import load_mock_json, tool_result
from mcp_servers.user_server import get_user_profile


_REFUND_REQUESTS: list[dict[str, Any]] = []


def get_invoice(
    invoice_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    if not invoice_id and not user_id:
        return tool_result(
            ok=False,
            action="get_invoice",
            error="invoice_id or user_id is required",
        )

    invoices = load_mock_json("invoices.json")
    if invoice_id:
        for invoice in invoices:
            if invoice["invoice_id"] == invoice_id:
                return tool_result(ok=True, action="get_invoice", data=invoice)
        return tool_result(
            ok=False,
            action="get_invoice",
            error=f"invoice not found: {invoice_id}",
        )

    matched = [invoice for invoice in invoices if invoice["user_id"] == user_id]
    if not matched:
        return tool_result(
            ok=False,
            action="get_invoice",
            error=f"invoice not found for user: {user_id}",
        )
    return tool_result(ok=True, action="get_invoice", data=matched)


def get_refund_status(user_id: str) -> dict[str, Any]:
    if not get_user_profile(user_id)["ok"]:
        return tool_result(
            ok=False,
            action="get_refund_status",
            error=f"user not found: {user_id}",
        )

    refunds = [request for request in _REFUND_REQUESTS if request["user_id"] == user_id]
    return tool_result(
        ok=True,
        action="get_refund_status",
        data={"user_id": user_id, "refund_requests": refunds},
    )


def create_refund_request(
    user_id: str,
    reason: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    if not get_user_profile(user_id)["ok"]:
        return tool_result(
            ok=False,
            action="create_refund_request",
            error=f"user not found: {user_id}",
            dry_run=dry_run,
        )

    proposal = {
        "user_id": user_id,
        "reason": reason,
        "status": "proposed" if dry_run else "created",
    }
    if not dry_run:
        proposal["refund_request_id"] = f"refund_{len(_REFUND_REQUESTS) + 1:04d}"
        _REFUND_REQUESTS.append(proposal)

    return tool_result(
        ok=True,
        action="create_refund_request",
        data=proposal,
        dry_run=dry_run,
    )

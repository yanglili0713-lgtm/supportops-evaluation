from mcp_servers.billing_server import (
    create_refund_request,
    get_invoice,
    get_refund_status,
)
from mcp_servers.logs_server import search_error_logs
from mcp_servers.ticket_server import create_ticket
from mcp_servers.user_server import (
    get_user_permissions,
    get_user_plan,
    get_user_profile,
)


def test_get_user_profile_by_user_id():
    result = get_user_profile("u_1001")

    assert result["ok"] is True
    assert result["action"] == "get_user_profile"
    assert result["data"]["email"] == "alice@example.com"
    assert result["error"] is None
    assert result["dry_run"] is False


def test_get_user_plan():
    result = get_user_plan("u_1001")

    assert result["ok"] is True
    assert result["data"] == {"user_id": "u_1001", "plan": "pro"}


def test_get_user_permissions():
    result = get_user_permissions("u_1001")

    assert result["ok"] is True
    assert "manage_team" in result["data"]["permissions"]


def test_get_invoice_by_invoice_id_or_user_id():
    by_invoice = get_invoice(invoice_id="inv_9001")
    by_user = get_invoice(user_id="u_1001")

    assert by_invoice["ok"] is True
    assert by_invoice["data"]["invoice_id"] == "inv_9001"
    assert by_user["ok"] is True
    assert by_user["data"][0]["user_id"] == "u_1001"


def test_refund_write_operation_defaults_to_dry_run():
    result = create_refund_request("u_1001", "用户申请 7 天内退款")

    assert result["ok"] is True
    assert result["action"] == "create_refund_request"
    assert result["dry_run"] is True
    assert result["data"]["status"] == "proposed"


def test_ticket_write_operation_defaults_to_dry_run():
    result = create_ticket("u_1001", "rag_upload_issue", "上传 PDF 后检索不到内容")

    assert result["ok"] is True
    assert result["action"] == "create_ticket"
    assert result["dry_run"] is True
    assert result["data"]["status"] == "proposed"


def test_search_logs_by_error_code():
    result = search_error_logs(error_code="EMBEDDING_FAILED")

    assert result["ok"] is True
    assert len(result["data"]) == 1
    assert result["data"][0]["user_id"] == "u_1001"


def test_missing_user_returns_ok_false_and_error():
    result = get_user_profile("u_missing")

    assert result["ok"] is False
    assert result["data"] is None
    assert "user not found" in result["error"]


def test_get_refund_status_for_existing_user():
    result = get_refund_status("u_1001")

    assert result["ok"] is True
    assert result["data"]["user_id"] == "u_1001"

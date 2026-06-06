import json
from pathlib import Path

from app.router import SUPPORTED_INTENTS, route_question


def test_api_key_invalid_routes_to_api_key_issue():
    result = route_question("API Key 失效了，接口一直返回 unauthorized")

    assert result["intent"] == "api_key_issue"
    assert result["confidence"] > 0
    assert "api key" in result["matched_keywords"]


def test_pdf_upload_no_recall_routes_to_rag_upload_issue():
    result = route_question("上传 PDF 后检索不到内容")

    assert result["intent"] == "rag_upload_issue"


def test_billing_refund_invoice_routes_to_billing_refund():
    queries = [
        "我要申请退款",
        "发票信息在哪里修改？",
        "这个月账单金额不对",
    ]

    for query in queries:
        assert route_question(query)["intent"] == "billing_refund"


def test_permission_denied_routes_to_permission_issue():
    result = route_question("团队成员打开项目时提示权限不足")

    assert result["intent"] == "permission_issue"


def test_expired_login_session_routes_to_login_issue():
    result = route_question("登录态过期后一直跳回登录页")

    assert result["intent"] == "login_issue"


def test_unknown_question_routes_to_unknown():
    result = route_question("今天办公室空调温度是多少？")

    assert result["intent"] == "unknown"
    assert result["confidence"] == 0.0
    assert result["matched_keywords"] == []


def test_pdf_upload_no_recall_is_not_permission_issue():
    result = route_question("上传 PDF 后检索不到内容")

    assert result["intent"] == "rag_upload_issue"
    assert result["intent"] != "permission_issue"
    assert result["confidence"] >= 0.7


def test_router_output_schema():
    result = route_question("部署失败并返回 500")

    assert set(result) == {"intent", "confidence", "reason", "matched_keywords"}
    assert result["intent"] in SUPPORTED_INTENTS
    assert isinstance(result["confidence"], float)
    assert isinstance(result["reason"], str)
    assert isinstance(result["matched_keywords"], list)


def test_gold_cases_route_to_expected_intents():
    gold_path = Path("data/gold_cases.jsonl")
    rows = [
        json.loads(line)
        for line in gold_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) >= 12
    for row in rows:
        assert route_question(row["query"])["intent"] == row["intent"]

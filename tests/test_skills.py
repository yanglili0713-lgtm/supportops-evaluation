from app.skill_loader import get_skill, list_skills
from app.skill_selector import select_skill


EXPECTED_SKILLS = {
    "refund_policy",
    "login_troubleshooting",
    "api_key_recovery",
    "rag_upload_debug",
    "escalation",
}

REQUIRED_SECTIONS = [
    "## 适用场景",
    "## 必须收集的信息",
    "## 可用 RAG 文档",
    "## 可用 MCP Mock Tools",
    "## 禁止事项",
    "## 处理步骤",
    "## 升级人工条件",
    "## 输出模板",
]


def test_loads_all_skill_documents():
    skills = list_skills()

    assert {skill["skill_name"] for skill in skills} == EXPECTED_SKILLS
    assert all(skill["path"].endswith("SKILL.md") for skill in skills)
    assert all(skill["content"] for skill in skills)


def test_each_skill_contains_required_sections():
    for skill in list_skills():
        for section in REQUIRED_SECTIONS:
            assert section in skill["content"], skill["skill_name"]


def test_billing_refund_selects_refund_policy():
    result = select_skill("billing_refund")

    assert result["skill_name"] == "refund_policy"
    assert result["confidence"] > 0


def test_rag_upload_issue_selects_rag_upload_debug():
    result = select_skill("rag_upload_issue")

    assert result["skill_name"] == "rag_upload_debug"


def test_api_key_issue_selects_api_key_recovery():
    result = select_skill("api_key_issue")

    assert result["skill_name"] == "api_key_recovery"


def test_login_issue_selects_login_troubleshooting():
    result = select_skill("login_issue")

    assert result["skill_name"] == "login_troubleshooting"


def test_unknown_selects_escalation():
    result = select_skill("unknown")

    assert result["skill_name"] == "escalation"


def test_todo_intents_select_escalation_with_reason():
    result = select_skill("permission_issue")

    assert result["skill_name"] == "escalation"
    assert "TODO" in result["reason"]


def test_missing_skill_name_returns_none():
    assert get_skill("does_not_exist") is None


def test_get_existing_skill_by_name():
    skill = get_skill("refund_policy")

    assert skill is not None
    assert skill["skill_name"] == "refund_policy"
    assert "create_refund_request" in skill["content"]

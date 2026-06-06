from app.memory import CaseState, update_case_state


def test_user_id_persists_across_multi_turn_dialogue():
    state = CaseState()

    update_case_state(state, "我的 user_id 是 u_1001")
    update_case_state(state, "上传 PDF 后检索不到内容")
    update_case_state(state, "我已经重新上传过，还是不行")

    assert state.user_id == "u_1001"
    assert "重新上传过" in state.attempted_steps


def test_plan_persists_after_later_turns():
    state = CaseState()

    update_case_state(state, "我是 pro 套餐用户，user_id 是 u_1001")
    update_case_state(state, "后来接口还是报错")

    assert state.plan == "pro"
    assert state.user_id == "u_1001"


def test_pdf_upload_records_uploaded_file_type():
    state = CaseState()

    update_case_state(state, "上传 PDF 后检索不到内容")

    assert state.uploaded_file_type == "PDF"


def test_embedding_failed_records_error_code():
    state = CaseState()

    update_case_state(state, "日志里出现 EMBEDDING_FAILED")

    assert state.error_code == "EMBEDDING_FAILED"


def test_missing_user_id_is_recorded():
    state = CaseState()

    update_case_state(state, "上传 PDF 后检索不到内容")

    assert "user_id" in state.missing_info


def test_invoice_id_and_router_intent_are_recorded():
    state = CaseState()

    update_case_state(
        state,
        "我要查 inv_9001 的退款状态",
        router_result={"intent": "billing_refund"},
    )

    assert state.invoice_id == "inv_9001"
    assert state.intent == "billing_refund"
    assert state.last_router_intent == "billing_refund"


def test_case_state_output_schema_contains_required_fields():
    state = CaseState()

    result = update_case_state(
        state,
        "我是 enterprise 套餐，user_id 是 u_1002，错误码 PERMISSION_DENIED",
        router_result={"intent": "permission_issue"},
    ).to_dict()

    assert set(result) == {
        "user_id",
        "plan",
        "intent",
        "error_code",
        "invoice_id",
        "uploaded_file_type",
        "attempted_steps",
        "missing_info",
        "last_router_intent",
        "current_decision",
    }
    assert result["plan"] == "enterprise"
    assert result["error_code"] == "PERMISSION_DENIED"

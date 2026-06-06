from __future__ import annotations

from app.memory import CaseState, update_case_state


def run_eval() -> dict:
    state = CaseState()
    turns = [
        ("我是 pro 套餐，user_id 是 u_1001", {"intent": "rag_upload_issue"}),
        ("上传 PDF 后检索不到内容", {"intent": "rag_upload_issue"}),
        ("日志里出现 EMBEDDING_FAILED，我也重新上传过", {"intent": "rag_upload_issue"}),
        ("现在还是搜不到任何内容", {"intent": "rag_upload_issue"}),
    ]
    for message, router_result in turns:
        update_case_state(state, message, router_result=router_result)

    checks = {
        "user_id_persisted": state.user_id == "u_1001",
        "plan_persisted": state.plan == "pro",
        "error_code_persisted": state.error_code == "EMBEDDING_FAILED",
        "uploaded_file_type_persisted": state.uploaded_file_type == "PDF",
        "attempted_steps_accumulated": "重新上传过" in state.attempted_steps,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]

    return {
        "name": "memory_regression_eval",
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "case_state": state.to_dict(),
    }


if __name__ == "__main__":
    print(run_eval())

import json

from app.tracing import TraceRecorder
from evals import memory_regression_eval, rag_grounding_eval, router_confusion_eval
from evals.run_all import run_all


def test_trace_recorder_saves_json(tmp_path):
    recorder = TraceRecorder(user_message="上传 PDF 后检索不到内容", runs_dir=tmp_path)
    recorder.record_router_result({"intent": "rag_upload_issue", "confidence": 0.9})
    recorder.record_selected_skill({"skill_name": "rag_upload_debug", "confidence": 0.9})
    recorder.record_case_state({"user_id": "u_1001", "uploaded_file_type": "PDF"})
    recorder.record_retrieved_citations(
        [{"doc_id": "rag_upload_troubleshooting", "chunk_id": "rag_upload_troubleshooting:0"}]
    )
    recorder.record_tool_call(
        "search_error_logs",
        {"error_code": "EMBEDDING_FAILED"},
        {"ok": True, "data": []},
    )
    recorder.record_final_answer("根据知识库和日志，建议检查 OCR。")
    recorder.add_warning("dry_run only")

    path = recorder.save()
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.exists()
    assert payload["run_id"] == recorder.run_id
    assert payload["user_message"] == "上传 PDF 后检索不到内容"
    assert payload["router_result"]["intent"] == "rag_upload_issue"
    assert payload["tool_calls"][0]["tool_name"] == "search_error_logs"
    assert payload["warnings"] == ["dry_run only"]


def test_run_all_generates_report():
    result = run_all()

    assert "tool_recall" in result
    assert "router_confusion" in result
    assert "memory_regression" in result
    assert "rag_grounding" in result

    report = "evals/report.md"
    with open(report, encoding="utf-8") as file:
        content = file.read()
    assert "Router accuracy" in content
    assert "Current known limitations" in content


def test_high_confidence_wrong_route_field_exists():
    result = router_confusion_eval.run_eval()

    assert "high_confidence_wrong_route" in result
    assert isinstance(result["high_confidence_wrong_route"], list)


def test_memory_regression_returns_structured_result():
    result = memory_regression_eval.run_eval()

    assert set(result) == {"name", "passed", "checks", "failed_checks", "case_state"}
    assert result["passed"] is True
    assert result["case_state"]["user_id"] == "u_1001"


def test_rag_grounding_returns_structured_result():
    result = rag_grounding_eval.run_eval()

    assert set(result) == {"name", "passed", "checks", "failed_checks", "details"}
    assert result["passed"] is True
    assert any(
        detail["required_doc"] == "rag_upload_troubleshooting"
        for detail in result["details"]
    )

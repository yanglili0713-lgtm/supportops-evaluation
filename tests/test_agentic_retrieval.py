import json
from pathlib import Path

from app.agent_loop import run_agent
from app.verifier import evidence_sufficiency_check


def test_agent_loop_runs_rag_upload_failed_case(tmp_path):
    result = run_agent(
        "user_id 是 u_1001，上传 PDF 后检索不到内容，错误码 EMBEDDING_FAILED",
        traces_dir=tmp_path,
    )

    assert result["router_result"]["intent"] == "rag_upload_issue"
    assert result["selected_skill"]["skill_name"] == "rag_upload_debug"
    assert any(citation["doc_id"] == "rag_upload_troubleshooting" for citation in result["citations"])
    assert result["graph_evidence"]
    assert any(call["tool_name"] == "search_error_logs" for call in result["tool_calls"])


def test_agent_loop_saves_trace_with_graph_evidence(tmp_path):
    result = run_agent(
        "user_id 是 u_1001，上传 PDF 后检索不到内容，错误码 EMBEDDING_FAILED",
        traces_dir=tmp_path,
    )
    trace_path = Path(result["trace_path"])
    payload = json.loads(trace_path.read_text(encoding="utf-8"))

    assert trace_path.exists()
    assert payload["router_result"]["intent"] == "rag_upload_issue"
    assert payload["selected_skill"]["skill_name"] == "rag_upload_debug"
    assert payload["graph_evidence"]


def test_evidence_sufficiency_detects_missing_citation():
    result = evidence_sufficiency_check(
        {
            "citations": [],
            "graph_evidence": [{"path": []}],
            "tool_calls": [],
            "needs_graph": True,
            "needs_tool": False,
        }
    )

    assert result["sufficient"] is False
    assert "citations" in result["missing_evidence"]
    assert result["next_action"] == "retry_retrieval"


def test_empty_graph_evidence_triggers_warning(tmp_path):
    result = run_agent("上传 PDF 后检索不到内容", traces_dir=tmp_path)

    assert "graph_rag" in result["plan"]["steps"]
    assert not result["graph_evidence"]
    assert any("graph evidence empty" in warning for warning in result["warnings"])


def test_write_operations_remain_dry_run(tmp_path):
    result = run_agent("完全无法判断的问题，需要人工处理", traces_dir=tmp_path)
    ticket_calls = [call for call in result["tool_calls"] if call["tool_name"] == "create_ticket"]

    assert ticket_calls
    assert all(call["result"]["dry_run"] is True for call in ticket_calls)

from __future__ import annotations

from app.agent_loop import run_agent


def run_eval() -> dict:
    result = run_agent(
        "user_id 是 u_1001，上传 PDF 后检索不到内容，错误码 EMBEDDING_FAILED",
        traces_dir="traces/runs",
    )
    checks = {
        "routed_to_rag_upload": result["router_result"]["intent"] == "rag_upload_issue",
        "selected_rag_upload_skill": result["selected_skill"]["skill_name"] == "rag_upload_debug",
        "has_citations": bool(result["citations"]),
        "has_graph_evidence": bool(result["graph_evidence"]),
        "called_logs_tool": any(call["tool_name"] == "search_error_logs" for call in result["tool_calls"]),
        "trace_saved": bool(result["trace_path"]),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    return {
        "name": "agentic_retry_eval",
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "warnings": result["warnings"],
    }


if __name__ == "__main__":
    print(run_eval())

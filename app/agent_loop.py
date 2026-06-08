from __future__ import annotations

from pathlib import Path

from app.evidence_planner import plan_retrieval
from app.memory import CaseState, update_case_state
from app.router import route_question
from app.skill_selector import select_skill
from app.tracing import TraceRecorder
from app.verifier import evidence_sufficiency_check
from graph.entity_linker import link_entities
from graph.graph_retriever import GraphRetriever
from mcp_servers.billing_server import get_invoice
from mcp_servers.logs_server import search_error_logs
from mcp_servers.ticket_server import create_ticket
from rag.chunker import chunk_documents
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import load_markdown_docs


def run_agent(
    user_message: str,
    case_state: CaseState | None = None,
    traces_dir: str | Path = "traces/runs",
    force_fallback_embedding: bool | None = None,
    offline: bool | None = None,
    mock_backend: bool | None = None,
) -> dict:
    state = case_state or CaseState()
    trace = TraceRecorder(user_message=user_message, runs_dir=traces_dir)

    router_result = route_question(user_message)
    update_case_state(state, user_message, router_result=router_result)
    selected_skill = select_skill(router_result["intent"])
    plan = plan_retrieval(user_message, state, router_result, selected_skill)

    trace.record_router_result(router_result)
    trace.record_selected_skill(selected_skill)
    trace.record_case_state(state.to_dict())

    retriever = _build_hybrid_retriever(
        force_fallback_embedding=force_fallback_embedding,
        offline=offline,
        mock_backend=mock_backend,
    )
    citations = _retrieve_citations(retriever, user_message)
    rewritten_query = None
    retries = 0
    while not citations and retries < plan["max_retries"]:
        rewritten_query = _rewrite_query(user_message, state)
        citations = _retrieve_citations(retriever, rewritten_query)
        retries += 1

    entities = link_entities(user_message, state.to_dict())
    graph_evidence = []
    if "graph_rag" in plan["steps"]:
        graph_evidence = GraphRetriever().retrieve(entities)
        if not graph_evidence and state.error_code:
            retry_entities = {"error_code": state.error_code}
            graph_evidence = GraphRetriever().retrieve(retry_entities)

    tool_calls = []
    if "logs_tool" in plan["steps"]:
        log_result = search_error_logs(user_id=state.user_id, error_code=state.error_code)
        tool_calls.append(
            {
                "tool_name": "search_error_logs",
                "args": {"user_id": state.user_id, "error_code": state.error_code},
                "result": log_result,
                "is_write": False,
            }
        )
        trace.record_tool_call("search_error_logs", {"user_id": state.user_id, "error_code": state.error_code}, log_result)

    if "billing_tool" in plan["steps"]:
        invoice_result = get_invoice(invoice_id=state.invoice_id, user_id=state.user_id)
        tool_calls.append(
            {
                "tool_name": "get_invoice",
                "args": {"invoice_id": state.invoice_id, "user_id": state.user_id},
                "result": invoice_result,
                "is_write": False,
            }
        )
        trace.record_tool_call("get_invoice", {"invoice_id": state.invoice_id, "user_id": state.user_id}, invoice_result)

    if "ticket_tool" in plan["steps"]:
        ticket_result = create_ticket(
            state.user_id or "unknown",
            router_result["intent"],
            user_message[:160],
            dry_run=True,
        )
        tool_calls.append(
            {
                "tool_name": "create_ticket",
                "args": {"user_id": state.user_id or "unknown", "dry_run": True},
                "result": ticket_result,
                "is_write": True,
            }
        )
        trace.record_tool_call("create_ticket", {"user_id": state.user_id or "unknown", "dry_run": True}, ticket_result)

    evidence = {
        "citations": citations,
        "graph_evidence": graph_evidence,
        "tool_calls": tool_calls,
        "needs_graph": "graph_rag" in plan["steps"],
        "needs_tool": any(step.endswith("_tool") for step in plan["steps"]),
    }
    verification = evidence_sufficiency_check(evidence)
    warnings = list(verification["warnings"])
    if rewritten_query:
        warnings.append(f"query_rewritten: {rewritten_query}")
    if "graph_evidence" in verification["missing_evidence"]:
        warnings.append("graph evidence empty after retry")
    if tool_calls and any(not call["result"].get("data") for call in tool_calls):
        warnings.append("one or more tool calls returned empty data")

    final_answer = _build_final_answer(router_result, selected_skill, citations, graph_evidence, tool_calls, verification)

    trace.record_retrieved_citations(citations)
    trace.record_graph_evidence(graph_evidence)
    trace.record_final_answer(final_answer)
    for warning in warnings:
        trace.add_warning(warning)
    trace_path = trace.save()

    return {
        "final_answer": final_answer,
        "router_result": router_result,
        "selected_skill": selected_skill,
        "case_state": state.to_dict(),
        "citations": citations,
        "graph_evidence": graph_evidence,
        "tool_calls": tool_calls,
        "warnings": warnings,
        "verification": verification,
        "plan": plan,
        "trace_path": str(trace_path),
    }


def _build_hybrid_retriever(
    force_fallback_embedding: bool | None = None,
    offline: bool | None = None,
    mock_backend: bool | None = None,
) -> HybridRetriever:
    docs = load_markdown_docs("data/docs")
    return HybridRetriever(
        chunk_documents(docs),
        alpha=0.6,
        force_fallback=force_fallback_embedding,
        offline=offline,
        mock_backend=mock_backend,
    )


def _retrieve_citations(retriever: HybridRetriever, query: str) -> list[dict]:
    return [
        {
            "doc_id": result.doc_id,
            "chunk_id": result.chunk_id,
            "source": result.source,
            "score": round(result.score, 4),
        }
        for result in retriever.search(query, top_k=3)
    ]


def _rewrite_query(user_message: str, state: CaseState) -> str:
    parts = [user_message]
    if state.intent == "rag_upload_issue":
        parts.append("RAG 上传失败 embedding 向量库 OCR")
    if state.error_code:
        parts.append(state.error_code)
    return " ".join(parts)


def _build_final_answer(
    router_result: dict,
    selected_skill: dict,
    citations: list[dict],
    graph_evidence: list[dict],
    tool_calls: list[dict],
    verification: dict,
) -> str:
    citation_docs = ", ".join(citation["doc_id"] for citation in citations) or "none"
    graph_paths = len(graph_evidence)
    tool_names = ", ".join(call["tool_name"] for call in tool_calls) or "none"
    return (
        f"intent={router_result['intent']} skill={selected_skill['skill_name']}. "
        f"citations={citation_docs}. graph_paths={graph_paths}. tools={tool_names}. "
        f"next_action={verification['next_action']}."
    )

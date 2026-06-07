from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.agent_loop import run_agent
from graph.entity_linker import link_entities
from graph.graph_retriever import GraphRetriever
from rag.chunker import chunk_documents
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import load_markdown_docs
from rag.pipeline import RAGPipeline


DOC_KEYWORDS = {
    "data/docs/api_key_guide.md": ["api key", "apikey", "key", "密钥", "401", "invalid"],
    "data/docs/error_code_manual.md": [
        "auth_expired",
        "api_key_invalid",
        "embedding_failed",
        "vector_write_failed",
        "permission_denied",
        "billing_required",
        "错误码",
    ],
    "data/docs/permission_guide.md": ["权限", "角色", "owner", "admin", "member", "permission"],
    "data/docs/rag_upload_troubleshooting.md": ["上传", "pdf", "rag", "检索", "embedding", "chunk", "ocr", "向量库"],
    "data/docs/refund_policy.md": ["退款", "账单", "invoice", "paid", "发票", "扣费", "80%", "企业套餐"],
}


def run_pipeline(pipeline_name: str, query: str) -> dict:
    if pipeline_name == "dummy":
        return _run_dummy(query)
    if pipeline_name == "naive":
        return _run_naive(query)
    if pipeline_name == "hybrid":
        return _run_hybrid(query)
    if pipeline_name == "graph":
        return _run_graph(query)
    if pipeline_name == "planner":
        return _run_planner(query)
    return _not_implemented(pipeline_name)


def _not_implemented(pipeline_name: str) -> dict:
    return {
        "answer": "Pipeline is not implemented yet.",
        "retrieved_docs": [],
        "route": "not_implemented",
        "raw": {"pipeline": pipeline_name, "status": "not_implemented"},
    }


def _run_dummy(query: str) -> dict:
    route = _route(query)
    retrieved_docs = _retrieve_docs(query, route)
    answer = _answer(query, route, retrieved_docs)
    return {
        "answer": answer,
        "retrieved_docs": retrieved_docs,
        "route": route,
        "raw": {"pipeline": "dummy"},
    }


def _run_naive(query: str) -> dict:
    results = _naive_pipeline().query(query, top_k=5)
    citations = _format_retrieval_results(results)
    return {
        "answer": _answer_from_citations("naive", citations),
        "retrieved_docs": _unique_sources(citations),
        "route": "naive",
        "raw": {"pipeline": "naive", "citations": citations},
    }


def _run_hybrid(query: str) -> dict:
    results = _hybrid_retriever().search(query, top_k=5)
    citations = _format_retrieval_results(results)
    return {
        "answer": _answer_from_citations("hybrid", citations),
        "retrieved_docs": _unique_sources(citations),
        "route": "hybrid",
        "raw": {"pipeline": "hybrid", "citations": citations},
    }


def _run_graph(query: str) -> dict:
    entities = link_entities(query)
    graph_evidence = GraphRetriever().retrieve(entities)
    return {
        "answer": _answer_from_graph(graph_evidence),
        "retrieved_docs": [],
        "route": "graph",
        "raw": {
            "pipeline": "graph",
            "entities": entities,
            "graph_evidence": graph_evidence,
        },
    }


def _run_planner(query: str) -> dict:
    result = run_agent(query, traces_dir=Path("traces/runs"))
    citations = result.get("citations", [])
    return {
        "answer": result.get("final_answer", ""),
        "retrieved_docs": _unique_sources(citations),
        "route": result.get("router_result", {}).get("intent", "planner"),
        "raw": {
            "pipeline": "planner",
            "router_result": result.get("router_result"),
            "selected_skill": result.get("selected_skill"),
            "case_state": result.get("case_state"),
            "citations": citations,
            "graph_evidence": result.get("graph_evidence", []),
            "tool_calls": result.get("tool_calls", []),
            "warnings": result.get("warnings", []),
            "verification": result.get("verification"),
            "plan": result.get("plan"),
            "trace_path": result.get("trace_path"),
        },
    }


@lru_cache(maxsize=1)
def _naive_pipeline() -> RAGPipeline:
    return RAGPipeline(docs_dir="data/docs")


@lru_cache(maxsize=1)
def _hybrid_retriever() -> HybridRetriever:
    docs = load_markdown_docs("data/docs")
    return HybridRetriever(chunk_documents(docs), alpha=0.6)


def _format_retrieval_results(results: list) -> list[dict]:
    return [
        {
            "doc_id": result.doc_id,
            "chunk_id": result.chunk_id,
            "source": result.source,
            "score": round(result.score, 4),
            "text": result.text,
        }
        for result in results
    ]


def _unique_sources(citations: list[dict]) -> list[str]:
    sources = []
    for citation in citations:
        source = citation.get("source")
        if source and source not in sources:
            sources.append(source)
    return sources


def _answer_from_citations(pipeline_name: str, citations: list[dict]) -> str:
    if not citations:
        return "知识库中没有足够证据回答该问题。"
    docs = ", ".join(_unique_sources(citations))
    snippets = " ".join(citation["text"].replace("\n", " ")[:120] for citation in citations[:2])
    return f"{pipeline_name} retrieved evidence from {docs}. Evidence summary: {snippets}"


def _answer_from_graph(graph_evidence: list[dict]) -> str:
    if not graph_evidence:
        return "GraphRAG found no graph evidence for this query."
    summaries = []
    for item in graph_evidence[:3]:
        labels = [node["label"] for node in item.get("path", [])]
        relationships = item.get("relationships", [])
        summaries.append(" -> ".join(labels + relationships))
    return f"GraphRAG found {len(graph_evidence)} graph paths: " + " | ".join(summaries)


def _route(query: str) -> str:
    text = query.lower()
    compact = text.replace(" ", "")
    if any(token in compact for token in ["apikey", "api_key", "密钥", "token", "secret", "credential"]):
        return "api_key_issue"
    if any(token in text for token in ["退款", "账单", "invoice", "发票", "billing_required"]):
        return "billing_refund"
    if any(token in text for token in ["上传", "pdf", "rag", "embedding", "vector_write_failed", "ocr"]):
        return "rag_upload_issue"
    if any(token in text for token in ["权限", "permission_denied", "owner", "admin", "member"]):
        return "permission_issue"
    if any(token in text for token in ["登录", "验证码", "auth_expired"]):
        return "login_issue"
    if any(token in text for token in ["支持哪些", "文件格式"]):
        return "general_faq"
    return "unknown"


def _retrieve_docs(query: str, route: str) -> list[str]:
    text = query.lower()
    docs = []
    for doc_path, keywords in DOC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            docs.append(doc_path)

    route_defaults = {
        "api_key_issue": ["data/docs/api_key_guide.md", "data/docs/error_code_manual.md"],
        "billing_refund": ["data/docs/refund_policy.md"],
        "rag_upload_issue": ["data/docs/rag_upload_troubleshooting.md", "data/docs/error_code_manual.md"],
        "permission_issue": ["data/docs/permission_guide.md", "data/docs/error_code_manual.md"],
        "login_issue": ["data/docs/error_code_manual.md"],
    }
    for doc_path in route_defaults.get(route, []):
        if doc_path not in docs:
            docs.append(doc_path)
    return docs[:5]


def _answer(query: str, route: str, retrieved_docs: list[str]) -> str:
    text = query.lower()
    compact = text.replace(" ", "")
    if _asks_for_secret(compact):
        return "无法确认或提供真实 secret、token、password、credential、API Key 等敏感信息；没有足够证据支持此类请求。"
    if "绕过" in text and "退款" in text:
        return "无法确认可绕过审核执行退款；退款或工单写操作应先 dry-run，并在用户确认后处理。"
    if route == "general_faq" and not retrieved_docs:
        return "知识库中没有足够证据回答该问题。"
    if route == "unknown":
        return "知识库中没有足够证据，无法确认该问题的答案。"

    if route == "api_key_issue":
        return (
            "API Key 失效可能与 key 被删除、过期、套餐、权限或环境不一致有关；"
            "应先确认 user_id、查询 key 状态、套餐和权限。API_KEY_INVALID 需要结合错误码手册确认。"
        )
    if route == "rag_upload_issue":
        return (
            "PDF 或 RAG 上传后检索不到内容，可能是解析失败、chunk 配置、embedding 失败、"
            "向量库写入失败、语义不匹配或扫描版 PDF 缺少 OCR；应查看上传日志、embedding 状态和向量写入数量。"
        )
    if route == "billing_refund":
        return (
            "退款需参考 7 天窗口、订单 paid 状态、企业套餐人工审核和 80% 使用比例；"
            "不能直接承诺退款成功，通常要先查询 invoice。"
        )
    if route == "permission_issue":
        return (
            "权限问题应先检查 owner、admin、member 角色和项目授权；PERMISSION_DENIED 表示权限不足，"
            "不要直接判断为系统故障，可引导联系管理员。"
        )
    if route == "login_issue":
        return "登录问题可参考 AUTH_EXPIRED：登录态过期通常需要重新登录；验证码问题应结合日志继续排查。"
    return "知识库中没有足够证据回答该问题。"


def _asks_for_secret(compact_query: str) -> bool:
    sensitive_terms = ["真实apikey", "真实token", "secret", "password", "credential", "告诉我用户"]
    return any(term in compact_query for term in sensitive_terms)

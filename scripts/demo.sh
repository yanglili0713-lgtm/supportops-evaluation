#!/usr/bin/env bash
set -e

echo "=============================================="
echo "SupportOps Agent Demo"
echo "=============================================="
echo

echo "[1/4] Run all tests"
uv run pytest -q
echo

echo "[2/4] Demo RAG query: 上传PDF后检索不到内容怎么办？"
printf '上传PDF后检索不到内容怎么办？\n' | uv run python -m app.cli
echo

echo "[3/5] Demo Hybrid RAG query"
uv run python - <<'PY'
from rag.chunker import chunk_documents
from rag.hybrid_retriever import HybridRetriever
from rag.ingest import load_markdown_docs

retriever = HybridRetriever(chunk_documents(load_markdown_docs("data/docs")))
for result in retriever.search("文档导入后答案没有依据", top_k=2):
    print({"doc_id": result.doc_id, "chunk_id": result.chunk_id, "source": result.source, "score": round(result.score, 4)})
PY
echo

echo "[4/6] Demo GraphRAG evidence"
uv run python - <<'PY'
from graph.entity_linker import link_entities
from graph.graph_retriever import GraphRetriever

entities = link_entities("u_1001 上传 PDF 失败，错误码 EMBEDDING_FAILED")
for item in GraphRetriever().retrieve(entities):
    print({"relationships": item["relationships"], "labels": [node["label"] for node in item["path"]]})
PY
echo

echo "[5/7] Demo Agentic retrieval loop"
uv run python - <<'PY'
from app.agent_loop import run_agent

result = run_agent("user_id 是 u_1001，上传 PDF 后检索不到内容，错误码 EMBEDDING_FAILED")
print(result["final_answer"])
print({"trace_path": result["trace_path"], "warnings": result["warnings"]})
PY
echo

echo "[6/7] Run eval pipeline"
uv run python -m evals.run_all
echo

echo "[7/7] Show generated eval report"
if [ -f "evals/report.md" ]; then
  sed -n '1,200p' evals/report.md
else
  echo "evals/report.md not found"
fi

echo
echo "Demo finished."

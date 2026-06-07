# SupportOps Agent Project Memory

## 1. Project Positioning

SupportOps Agent is an enterprise support and operations agent project for customer support, incident troubleshooting, ticket context, logs, and knowledge-base retrieval. The current codebase combines multi-source knowledge retrieval, mock tool calls, structured case memory, rule-based routing, evidence checks, tracing, and small eval scripts.

The project is positioned around realistic agent engineering problems: unstable RAG recall, wrong high-confidence routing, lost multi-turn case information, missing tool recall, dry-run safety for write operations, and observable traces/evals for debugging agent behavior.

## 2. What This Project Is Not

- It is not a pure prompt demo.
- It is not a Dify/low-code wrapper. The repo contains Python implementations plus workflow comparison docs.
- It is not meant to keep adding more RAG terminology without measurable behavior. Existing RAG, Hybrid RAG, GraphRAG, and planner pieces are small local implementations with tests/evals.

## 3. Existing Capabilities

- Agent loop: `app/agent_loop.py` runs routing, case-state update, skill selection, retrieval planning, Hybrid RAG retrieval, optional GraphRAG retrieval, selected mock tool calls, evidence verification, answer summary generation, and trace saving.
- Router: `app/router.py` provides an explainable keyword router for `login_issue`, `billing_refund`, `api_key_issue`, `rag_upload_issue`, `permission_issue`, `deployment_error`, `general_faq`, and `unknown`. It returns intent, confidence, reason, and matched keywords.
- Memory: `app/memory.py` maintains a structured `CaseState` with fields such as `user_id`, `plan`, `intent`, `error_code`, `invoice_id`, `uploaded_file_type`, `attempted_steps`, and `missing_info`.
- Skill loader / selector: `app/skill_loader.py` loads `skills/*/SKILL.md`; `app/skill_selector.py` maps several intents to skills and routes `permission_issue` / `deployment_error` to `escalation` as TODO-phase skills.
- Tracing: `app/tracing.py` records router result, selected skill, case state, citations, graph evidence, tool calls, final answer, and warnings into `traces/runs/*.json`.
- Verifier: `app/verifier.py` checks whether citations, graph evidence, and tool calls are present when needed, and warns if write tools are not dry-run.
- RAG pipeline: `rag/ingest.py`, `rag/chunker.py`, `rag/retriever.py`, and `rag/pipeline.py` load Markdown docs, chunk them, run BM25 retrieval, and return citation metadata.
- Hybrid retriever: `rag/hybrid_retriever.py`, `rag/vector_store.py`, and `rag/reranker.py` combine BM25 with an in-memory token vector store and a lightweight reranker.
- GraphRAG: `graph/` contains an in-memory graph implementation, entity linker, graph retriever, optional Neo4j adapter placeholder, and Neo4j-style schema documentation.
- MCP mock servers: `mcp_servers/` exists with user, billing, logs, and ticket mock tools. Write operations such as refund request and ticket creation default to `dry_run=True`.
- Skills: `skills/` contains SOP-style skill files for API key recovery, escalation, login troubleshooting, RAG upload debugging, and refund policy.
- Workflow docs: `workflows/` contains Dify, Coze, and workflow comparison documents.
- Tests: `tests/` contains focused pytest files for retrieval, routing, memory, skills, MCP servers, tracing/evals, Hybrid RAG, GraphRAG, agentic retrieval, pipeline, and workflow docs.

## 4. Existing Knowledge Sources and Data

- `data/docs/api_key_guide.md`: API Key failure causes and troubleshooting steps.
- `data/docs/error_code_manual.md`: common error codes including `AUTH_EXPIRED`, `API_KEY_INVALID`, `EMBEDDING_FAILED`, `VECTOR_WRITE_FAILED`, `PERMISSION_DENIED`, and `BILLING_REQUIRED`.
- `data/docs/permission_guide.md`: team roles and permission guidance.
- `data/docs/rag_upload_troubleshooting.md`: reasons why uploaded PDFs may not be retrievable, including parsing, chunking, embedding failure, vector write failure, semantic mismatch, and missing OCR.
- `data/docs/refund_policy.md`: refund window, paid-order requirement, enterprise review, usage-ratio constraint, and warning that the agent must not promise refund success.
- `data/gold_cases.jsonl`: 13 router gold cases covering API key, RAG upload, billing/refund, permission, login, deployment, general FAQ, and unknown examples.
- `data/mock/invoices.json`: mock paid invoices for `u_1001` and `u_1002`, with amount, paid date, and usage ratio.
- `data/mock/logs.json`: mock error logs for `EMBEDDING_FAILED` and `PERMISSION_DENIED`.
- `data/mock/users.json`: mock user profile, plan, role, and team data for `u_1001` and `u_1002`.
- `data/graph_seed.json`: seed graph data for users, team, project, upload job, error codes, services, ticket, skill, and SOP step.
- `skills/api_key_recovery/SKILL.md`: SOP for API key failures.
- `skills/escalation/SKILL.md`: fallback/escalation SOP, including TODO notes for permission and deployment dedicated skills.
- `skills/login_troubleshooting/SKILL.md`: SOP for login failures.
- `skills/rag_upload_debug/SKILL.md`: SOP for RAG upload/retrieval failures.
- `skills/refund_policy/SKILL.md`: SOP for billing and refund handling.

## 5. Existing Evaluation Files

- `evals/common.py`: loads `data/gold_cases.jsonl` and normalizes `expected_intent`.
- `evals/rag_grounding_eval.py`: checks whether basic BM25 RAG returns citations and required docs for PDF upload, refund, and API Key questions.
- `evals/hybrid_rag_eval.py`: checks Hybrid RAG citation preservation and expected-doc recall, including a semantic paraphrase case.
- `evals/graphrag_eval.py`: checks graph retrieval paths for user/project/upload-job context and error/service/ticket context.
- `evals/agentic_retry_eval.py`: runs `run_agent` on a RAG upload failure case and checks routing, skill selection, citations, graph evidence, logs tool call, and trace path.
- `evals/router_confusion_eval.py`: builds a confusion matrix from gold cases and records high-confidence wrong routes.
- `evals/memory_regression_eval.py`: checks that multi-turn case state preserves user id, plan, error code, uploaded file type, and attempted steps.
- `evals/tool_recall_eval.py`: currently approximates tool recall through intent-routing accuracy over gold cases.
- `evals/run_all.py`: aggregates the evals above and writes `evals/report.md`.

These evals are useful smoke/regression checks, but they are small rule-based checks rather than a unified benchmark.

## 6. Current RAG / GraphRAG / Agentic Planner Structure

- Naive/basic RAG structure: `RAGPipeline` loads Markdown files from `data/docs`, chunks them with fixed character windows and overlap, then uses `BM25Retriever` to return `RetrievalResult` objects with `doc_id`, `chunk_id`, `source`, text, and score. Tokenization is mixed Chinese/English, with English/numbers as word tokens and Chinese as single-character tokens.
- Hybrid RAG structure: `HybridRetriever` runs BM25 and `SimpleVectorStore` in parallel, normalizes scores, merges by chunk, and reranks results. The vector store is an in-memory token-vector fallback with hand-written semantic aliases, not a production embedding service.
- GraphRAG structure: `graph/build_graph.py` builds an in-memory graph from `data/graph_seed.json`; `graph/entity_linker.py` extracts ids such as user id, error code, service id, ticket id, and project id; `graph/graph_retriever.py` returns path-style evidence for users, error codes, and services. `graph/schema.cypher` documents a Neo4j-style schema, while `graph/neo4j_adapter.py` is an optional adapter placeholder.
- Agentic retrieval / evidence planner structure: `app/evidence_planner.py` is an initial deterministic planner. It starts with BM25/vector retrieval and conditionally adds graph retrieval, logs, billing, ticket, or escalation steps based on intent, case state, and selected skill. `app/agent_loop.py` performs a simple retry with query rewrite when citations are empty and runs `evidence_sufficiency_check` before building the final answer summary.

## 7. Current Gaps

- No unified SupportOpsBench yet.
- No four-way pipeline ablation table for naive / hybrid / graph / planner.
- Metrics need clearer definitions for evidence recall, refusal accuracy, route accuracy, tool recall, and grounding.
- Failure case analysis is still lightweight and scattered across small eval outputs and challenge docs.
- Trace replay/reporting is not unified into a single replayable evaluation artifact.
- Resume-ready project summary exists in `docs/resume_description.md`, but it is not yet backed by a benchmark-style results table.
- Permission and deployment dedicated skills are still TODO-phase according to `app/skill_selector.py` and `skills/escalation/SKILL.md`.
- Tool recall eval is currently routed-intent based, not a full agent tool-orchestration benchmark.
- GraphRAG uses in-memory seed data; Neo4j integration remains a schema/adapter placeholder.
- Agentic planner is a deterministic local planner, not an LLM policy or learned planner.

## 8. Next Steps

1. Add SupportOpsBench without breaking the existing `evals/` package.
2. Add `supportops_metrics.py`, `supportops_adapters.py`, and `supportops_run_eval.py`.
3. Run a dummy pipeline first.
4. Then connect naive / hybrid / graph / planner pipelines.
5. Output `ablation_results.md` and `failure_cases.md`.

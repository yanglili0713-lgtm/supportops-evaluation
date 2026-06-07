# SupportOps Evaluation：面向客服/运维工单的 RAG 检索与诊断评测框架

SupportOps Evaluation 是一个本地可复现的 RAG 检索与诊断评测框架，用于比较 dummy、naive RAG、hybrid RAG、GraphRAG、planner 五组 pipeline 在同一批客服/运维工单 case 上的表现。

这个项目的核心是 Evaluation / Benchmark / Pipeline Comparison / Trace / Failure Analysis。它不是课程售后客服业务系统，也不是普通聊天机器人。

## What It Evaluates

当前使用 80-case SupportOpsBench seed benchmark，数据位于 `evals/supportops_bench.yaml`。Benchmark 覆盖：

- FAQ
- API Key recovery
- credential/token handling
- permission issue
- login issue
- refund policy
- RAG upload failure
- incident diagnosis
- multi-document diagnosis
- no-answer
- security boundary

当前实现保留 YAML benchmark，并通过 `run_eval.py` 中的 schema adapter 映射为统一评测字段。字段说明见 `benchmark/label_schema.md`。

## Run

```bash
python run_eval.py
python run_eval.py --pipelines dummy,naive,hybrid,graph,planner
python run_eval.py --out-dir reports --trace-dir traces
pytest
```

默认运行五组 pipeline，并生成统一三件套：

- `reports/report.json`
- `traces/trace.jsonl`
- `reports/failure_analysis.md`

## Pipelines

- `dummy`: Rule-based sanity baseline，用于验证 benchmark harness 和指标链路，不代表真实 Agent 能力。它不是 weak baseline，也不是 oracle baseline：dummy 不读取 `expected_docs`、gold label 或 benchmark answer，但它使用手写规则和文档 taxonomy，因此在当前 seed benchmark 上分数会偏高。
- `naive RAG`: 基础 BM25/关键词检索 pipeline，重点观察基础 evidence recall。
- `hybrid RAG`: BM25 + 本地 token-vector 融合检索，并做轻量 rerank，用于比较 recall 与 precision tradeoff。在当前 5-doc seed corpus 上，doc-level Recall@5 / Precision@5 可能与 naive 相同，因为评测按 doc source 去重且 `top_k=5`，粒度较粗；hybrid 的差异主要体现在 chunk、ranking 和 score。
- `GraphRAG`: Lightweight in-memory graph retrieval layer，用于 entity neighbor expansion 和 evidence aggregation。它更偏 evidence concentration，不保证覆盖所有弱表达 case；它不是 Neo4j 生产级图数据库，也不声称具备生产 GraphRAG 能力。
- `planner`: Demo-level deterministic planner/agent loop，支持 basic intent routing、case state、skill selection、evidence planning、tool candidate selection、basic refusal handling、verification 和 trace recording。当前 Route Accuracy 暴露出关键词泛化不足。

## Metrics

- `Evidence Recall@5`: top-5 retrieved documents 中命中 expected evidence documents 的比例。
- `Evidence Precision@5`: top-5 retrieved documents 中相关 evidence documents 的比例。
- `Refusal Accuracy`: no-answer/security-boundary case 是否正确拒答，answerable case 是否避免误拒答。当前是基于 refusal marker 的 baseline safety metric，不是严格安全验证。
- `Route Accuracy`: route_intent 是否等于 gold_intent。该指标主要适用于 routing-capable pipelines，例如 dummy 和 planner；retrieval-only pipeline 会报告 `N/A`。
- `Latency`: 每条 case 在单个 pipeline 下的本地执行耗时，报告 avg/p50/p95/max。

## Output Contract

`reports/report.json` 汇总五组 pipeline 的平均指标：

- `case_count`
- `evidence_recall_at_5`
- `evidence_precision_at_5`
- `refusal_accuracy`
- `route_accuracy`
- `average_latency_ms`

`traces/trace.jsonl` 每行记录一个 case 在一个 pipeline 下的执行结果，包含：

- `case_id`
- `pipeline`
- `query`
- `gold_intent`
- `route_intent`
- `expected_doc_ids`
- `retrieved_doc_ids`
- `answerability`
- `refusal_decision`
- `metrics`
- `latency_ms`
- `decision_notes`

`reports/failure_analysis.md` 自动读取 report 和 trace，生成：

- Overview
- Naive/Hybrid high recall but low precision cases
- GraphRAG evidence concentration analysis
- Planner route generalization failures
- No-answer / security boundary refusal failures
- Latency tradeoff
- Next optimization plan

## Local-Only Boundary

The project does not call real external APIs and does not use real user data, order data, credentials, secrets, or private production logs. Mock tools and benchmark cases are simulated local data.

No heavyweight framework is required. The implementation intentionally avoids LangChain, LlamaIndex, Neo4j, and production service dependencies.

## Existing Modules

- `evals/supportops_bench.yaml`: 80-case seed benchmark.
- `evals/supportops_run_eval.py`: Existing single-pipeline eval runner.
- `evals/supportops_adapters.py`: Adapter for dummy, naive, hybrid, graph, and planner pipelines.
- `evals/supportops_metrics.py`: Metric definitions.
- `evals/failure_analysis.py`: Automatic failure analysis generator.
- `run_eval.py`: Unified five-pipeline runner and schema adapter.
- `rag/`: BM25, hybrid retrieval, vector fallback, chunking.
- `graph/`: In-memory graph seed, entity linker, graph retriever.
- `app/`: Router, memory, planner loop, verifier, trace recorder.
- `mcp_servers/`: Local mock tools with dry-run write behavior.
- `tests/`: Unit and smoke tests.

## Interpretation

This repository supports resume claims about building a local SupportOps evaluation framework with benchmark cases, pipeline comparison, trace output, metrics, and failure analysis.

It should not be described as a production customer-support platform. The benchmark is a seed benchmark, GraphRAG is a lightweight in-memory retrieval layer, the planner is demo-level and deterministic rather than LLM-driven, and the verifier/refusal checks are baseline diagnostics rather than strict answer-faithfulness or safety proofs.

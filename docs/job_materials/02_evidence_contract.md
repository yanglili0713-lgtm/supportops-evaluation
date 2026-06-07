# Evidence Contract

| Claim | Can Write? | Evidence Files | Metrics | Interview Risk | Safe Wording |
| --- | --- | --- | --- | --- | --- |
| 我做了 SupportOps Agent。 | yes | `README.md`, `docs/PROJECT_MEMORY.md`, `app/agent_loop.py`, `app/router.py`, `app/memory.py`, `app/tracing.py` | tests and eval reports | 中等：要说明是 demo / local project，不是线上系统。 | 构建面向客服/运维工单场景的 SupportOps Agent 可复现 demo。 |
| 我实现了 RAG。 | yes | `rag/pipeline.py`, `rag/retriever.py`, `rag/chunker.py`, `data/docs/`, `evals/rag_grounding_eval.py` | naive Evidence Recall@5=0.975 on 20-case seed benchmark | 低到中：需要解释 tokenizer、chunk、citation。 | 实现基于 Markdown 知识库的 BM25 RAG 与 citation 返回。 |
| 我实现了 Hybrid RAG。 | yes | `rag/hybrid_retriever.py`, `rag/vector_store.py`, `rag/reranker.py`, `evals/hybrid_rag_eval.py` | hybrid Evidence Recall@5=0.975, Precision@5=0.2971 | 中：token-vector 不是生产 embedding。 | 实现 BM25 + 本地 token-vector 的 Hybrid Retrieval baseline。 |
| 我实现了 GraphRAG。 | cautious | `graph/`, `data/graph_seed.json`, `evals/graphrag_eval.py`, `evals/supportops_adapters.py` | GraphRAG Evidence Recall@5=0.95, Precision@5=0.9118 | 高：是 in-memory seed graph，不是完整 Neo4j 生产图谱。 | 实现 in-memory GraphRAG evidence pipeline，并用 Neo4j-style schema 文档化。 |
| 我实现了 Agentic Planner。 | cautious | `app/evidence_planner.py`, `app/agent_loop.py`, `reports/ablation_results.md` | Planner Route Accuracy=0.9, Evidence Recall@5=0.925 | 高：planner 是 deterministic local planner，不是 LLM policy。 | 实现 deterministic agentic retrieval planner，按 intent/skill/case_state 选择 evidence steps。 |
| 我设计了 SupportOpsBench。 | yes | `docs/benchmark_design.md`, `evals/supportops_bench.yaml`, `evals/supportops_run_eval.py` | 20 cases, five pipelines | 中：必须强调 seed benchmark。 | 设计 20-case SupportOpsBench seed benchmark 与统一评测入口。 |
| 我做了五组 pipeline 消融。 | yes | `reports/ablation_results.md`, `reports/eval_*_results.json`, `evals/supportops_adapters.py` | dummy/naive/hybrid/graph/planner result table | 中：dummy 高分不能当能力。 | 对五组 pipeline 做初步消融；dummy 仅用于 harness sanity check。 |
| 我实现了 Evidence Recall@5。 | yes | `evals/supportops_metrics.py`, `tests/test_supportops_eval.py` | reported for all five pipelines | 低：定义简单，需要能讲清 expected_docs/top5。 | 实现并报告 Evidence Recall@5。 |
| 我实现了 Evidence Precision@5。 | yes | `evals/supportops_metrics.py`, `tests/test_supportops_eval.py`, `docs/benchmark_design.md` | GraphRAG Precision@5=0.9118 | 低到中：no-answer cases 返回 N/A。 | 增加 Evidence Precision@5，用于暴露 top-k evidence noise。 |
| 我实现了 Refusal Accuracy。 | yes | `evals/supportops_metrics.py`, `evals/supportops_bench.yaml` | real pipelines Refusal Accuracy=0.8 on seed benchmark | 中：refusal markers 是规则式，不是安全评测。 | 在 seed benchmark 中加入 no-answer/security cases 并计算 Refusal Accuracy。 |
| 我实现了 Route Accuracy。 | yes | `evals/supportops_metrics.py`, `tests/test_supportops_eval.py`, `reports/ablation_results.md` | Planner Route Accuracy=0.9; retrieval-only pipelines N/A | 中：必须说明只适用于 planner/router。 | 对 planner/router pipeline 报告 Route Accuracy，对 retrieval-only pipeline 标为 N/A。 |
| 我实现了 latency 指标。 | yes | `evals/supportops_run_eval.py`, `evals/supportops_metrics.py`, `reports/ablation_results.md` | avg/p50/p95/max latency | 中：本地运行低延迟不等于生产 SLA。 | 记录本地 eval latency summary，用于比较 pipeline 开销。 |
| 我优化了 GraphRAG evidence-to-document mapping。 | yes | `evals/supportops_adapters.py`, `tests/test_supportops_eval.py`, `reports/failure_cases.md` | GraphRAG Recall@5=0.95, Precision@5=0.9118 | 中到高：当前是保守规则映射，不是 span-level grounding。 | 将 graph evidence、entities、query signals 保守映射到 `data/docs/*.md`。 |
| 我做了 leakage check。 | cautious | `evals/supportops_bench.yaml`, `reports/failure_cases.md` | no direct leakage metric | 高：没有独立 leakage audit 脚本。 | 谨慎写：区分 dummy rule baseline 与真实 pipeline，标注 dummy 高分不能作为能力证据。 |
| 我做了 trace replay。 | cautious | `app/tracing.py`, `evals/supportops_run_eval.py`, `traces/*.jsonl`, `README.md` | trace files exist; no full replay assertion yet | 高：当前更像 trace recording/reporting，不是完整 replay framework。 | 实现 trace recording 与 JSONL eval trace；trace replay 需补证据后写。 |
| 我能处理无答案拒答和安全边界。 | cautious | `evals/supportops_bench.yaml`, `evals/supportops_metrics.py`, `reports/failure_cases.md`, `app/verifier.py` | Refusal Accuracy=0.8 on real pipelines | 高：只有少量 seed cases。 | 在 seed benchmark 中覆盖 no-answer/security refusal，并通过 verifier/dry-run 降低越权风险。 |
| 我做了生产级系统。 | no | None | None | 极高：没有上线、监控、权限、用户流量、SLA 证据。 | 不能写。写“可复现工程 demo / seed benchmark / 本地评测闭环”。 |
| 我显著提升了业务效率。 | no | None | None | 极高：没有业务 baseline、用户日志或效率指标。 | 不能写。写“在 seed benchmark 上比较不同 pipeline 的 evidence、route、refusal 与 latency 差异”。 |


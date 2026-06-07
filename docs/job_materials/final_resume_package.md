# Final Resume Package

## Project Name Recommendation

1. SupportOps Agent: 面向客服/运维工单的多源知识检索与故障诊断 Agent
2. IncidentOps GraphRAG Agent: 面向故障工单的多源证据检索与诊断 Agent
3. SupportOpsBench-driven RAG Agent Evaluation System

Recommended: **SupportOps Agent: 面向客服/运维工单的多源知识检索与故障诊断 Agent**

Reason: this name covers the actual project scope: router, memory, skills, mock tools, RAG, Hybrid RAG, GraphRAG, planner, trace, and SupportOpsBench. It is broader and safer than making GraphRAG the only headline.

## Short Resume Version: 4 Bullets

- 构建面向客服/运维工单场景的 SupportOps Agent 可复现 demo，串联 intent router、structured case memory、SOP skills、mock tools、BM25/Hybrid RAG、in-memory GraphRAG、deterministic planner、verifier 与 trace output。
- 设计 SupportOpsBench v2.4 80-case seed benchmark，覆盖 FAQ、API Key、credential/token、权限、登录、退款、RAG 上传、incident diagnosis、多文档诊断、no-answer 与 security boundary，并标注 seen/unseen/no_answer、easy/medium/hard 和 multi-doc case。
- 实现 dummy、naive RAG、hybrid RAG、GraphRAG、planner 五组 pipeline 的统一评测入口，报告 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 与本地 latency，并输出 JSON report / JSONL trace。
- 在 80-case seed benchmark 上完成初步消融：naive/hybrid Evidence Recall@5=1.0000 但 Precision@5=0.2924，GraphRAG Precision@5=0.8542、Recall@5=0.8646，Planner Evidence Recall@5=0.9625、Route Accuracy=0.6250，并记录 failure analysis。

## Strong Resume Version: 6 Bullets

- 实现 SupportOps / IncidentOps Agent 工程 demo，将 router、case-state memory、skill selection、mock enterprise tools、retrieval pipeline、evidence verifier 和 trace recorder 拆成可测试模块，聚焦 RAG 召回不稳、错误路由、多轮状态丢失、工具写操作安全和可观测性问题。
- 基于 `data/docs/*.md` 搭建 BM25 RAG 与 BM25 + local token-vector Hybrid Retrieval baseline，保留 `doc_id/chunk_id/source/score/text` citation，并通过 tests/evals 验证 expected-doc recall 与 citation 输出。
- 实现 in-memory GraphRAG evidence pipeline，使用 seed graph 表达 user/team/project/upload job/error code/service/ticket/skill 等关系，并在 eval adapter 中将 graph evidence、linked entities 和 query signals 保守映射到真实 `data/docs/*.md` evidence paths。
- 设计 SupportOpsBench v2.4 80-case seed benchmark 与统一 runner，覆盖 11 类任务、27 个 multi-doc case、12 个 no-answer/security refusal case，并增加 benchmark quality tests 保证 case count、连续 ID、expected docs、split 与 difficulty 覆盖。
- 对 dummy、naive RAG、hybrid RAG、GraphRAG、planner 五组 pipeline 做可复现消融，区分 retrieval-only pipeline 与 planner/router pipeline 的 Route Accuracy 适用性，避免把检索系统误判为路由失败。
- 输出 ablation report 与 failure cases，定位 high-recall/low-precision retrieval、GraphRAG source-span 缺失、Planner Route Accuracy=0.6250、规则式 refusal metric 和本地 latency 稳定性等后续优化点。

## Conservative Resume Version: 3 Bullets

- 构建面向客服/运维工单的 SupportOps Agent 本地 demo，覆盖 RAG 检索、结构化 case memory、SOP skill、mock tools、verifier、trace output 和小规模离线 eval。
- 设计 80-case SupportOpsBench seed benchmark，对 dummy、naive RAG、hybrid RAG、in-memory GraphRAG、planner 五组 pipeline 做初步消融，报告 Evidence Recall/Precision、Refusal、Route 和 latency。
- 补充 Dify/Coze-style workflow prototype artifacts，用于说明同一 SupportOps 流程如何拆成低代码节点；该部分是 prototype design artifact，不是生产部署。

## Technical Stack Wording

Recommended wording:

```text
Python / Pytest / RAG / BM25 / Hybrid Retrieval / In-memory GraphRAG / Deterministic Agentic Planner / Tool Calling Mock / Evaluation Metrics / Trace Output
```

More concise wording:

```text
Python / RAG / Hybrid Retrieval / GraphRAG / Agentic Planner / Tool Calling / Evaluation / Trace
```

Do not write:

```text
LangGraph / Neo4j production graph / Milvus / Redis / LoRA / Dify production deployment / Coze production deployment
```

Safe note: the repo contains a Neo4j-style schema and optional placeholder adapter, but the actual evaluated GraphRAG path is in-memory. The Dify/Coze files are prototype schemas and comparison docs, not official exports or deployments.

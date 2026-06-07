# SupportOps Agent Resume Bullets

## A. 简历短版

- 构建面向客服/运维工单场景的 SupportOps Agent demo，串联 Router、RAG/Hybrid Retrieval、GraphRAG、Agentic Planner、verifier 与 trace 记录。
- 设计 20-case SupportOpsBench seed benchmark，对比 dummy、naive RAG、Hybrid RAG、GraphRAG、Planner 五组 pipeline 的 evidence、refusal、route 与 latency。
- 在 20-case seed benchmark 上，naive/hybrid Evidence Recall@5=0.975；GraphRAG Evidence Recall@5=0.95、Precision@5=0.9118。
- 在同一 seed benchmark 上，Planner Route Accuracy=0.9；同时记录 Refusal Accuracy、p95 latency 与 failure cases，用于后续扩展评测。

## B. 简历强版：AI Agent / RAG 工程岗位

- 实现 SupportOps Agent 可复现工程 demo，覆盖 BM25 RAG、BM25+token-vector Hybrid Retrieval、in-memory GraphRAG、deterministic Agentic Planner、SOP skill selection 与 MCP mock tools。
- 设计 SupportOpsBench seed benchmark 与统一评测入口，支持五组 pipeline 消融，输出 JSON report、JSONL trace，并区分 retrieval-only pipeline 与 planner/router pipeline 的 Route Accuracy 适用性。
- 新增 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 与 latency summary，避免只用 recall 掩盖 noisy retrieval；20-case seed benchmark 中 GraphRAG Precision@5=0.9118。
- 优化 GraphRAG evidence-to-document mapping，将 graph path、linked entities 与 query signals 保守映射到 `data/docs/*.md`，使 GraphRAG 的 Evidence Recall@5 从早期低值提升到 0.95。
- 通过 verifier、dry-run write tools、no-answer refusal cases、failure analysis 与 trace recording，定位拒答、路由、证据映射和 planner latency 的可靠性问题。

## C. 保守版

- 构建面向客服/运维工单的 SupportOps Agent 可复现 demo，重点验证 RAG 检索、结构化 case memory、SOP skill、mock tool、verifier 与 trace 的工程闭环。
- 设计 20-case SupportOpsBench seed benchmark，覆盖 API Key、RAG 上传、退款、权限、登录、多文档诊断、无答案拒答和安全边界等任务。
- 完成 naive RAG、Hybrid RAG、GraphRAG、Planner 五组 pipeline 的初步消融分析，报告 Evidence Recall/Precision、Refusal、Route 与 latency。
- 当前结果只作为 seed benchmark 初步证据，不写生产级结论；下一步计划扩展到 80-120 cases、补 citation precision 与 answer support checking。


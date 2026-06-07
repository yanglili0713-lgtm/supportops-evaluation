# Resume Summary

## Version A: Current Honest Version

SupportOps Agent：面向客服/运维工单的多源知识检索与故障诊断 Agent

- 构建面向客服/运维工单的多源 Agent 系统，覆盖 router、memory、skill selection、tool calling、RAG、Hybrid RAG、GraphRAG、agentic retrieval planner 与 trace replay。
- 设计 SupportOpsBench seed benchmark，覆盖 FAQ、API key、credential/token、权限、登录、退款、RAG 上传、incident diagnosis、多文档诊断、无答案拒答与安全边界等任务类型。
- 实现统一评测入口，支持 dummy、naive RAG、hybrid RAG、GraphRAG、planner 五组 pipeline 对照，输出 JSON 报告与 JSONL trace。
- 在 20-case seed benchmark 上完成初步消融，验证 naive/hybrid 的文档召回稳定性、planner 的路由能力，并优化 graph evidence 到真实文档路径的保守映射，同时定位 keyword-oriented metric、planner latency 等后续优化点。

## Version B: With Numbers Placeholder

- 在扩展后的 SupportOpsBench 上，对比 Naive RAG、Hybrid RAG、GraphRAG 与 Agentic Planner，在 Evidence Recall@5、Refusal Accuracy、Route Accuracy 和 p95 latency 上形成可复现实验报告。

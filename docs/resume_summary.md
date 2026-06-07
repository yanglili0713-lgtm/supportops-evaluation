# Resume Summary

## Version A: Current Honest Version

SupportOps Agent：面向客服/运维工单的多源知识检索与故障诊断 Agent

- 构建面向客服/运维工单的多源 Agent 系统，覆盖 router、memory、skill selection、tool calling、RAG、Hybrid RAG、GraphRAG、agentic retrieval planner 与 trace replay。
- 设计 SupportOpsBench v2.4 80-case seed benchmark，覆盖 FAQ、API key、credential/token、权限、登录、退款、RAG 上传、incident diagnosis、多文档诊断、无答案拒答与安全边界等任务类型。
- 实现统一评测入口，支持 dummy、naive RAG、hybrid RAG、GraphRAG、planner 五组 pipeline 对照，输出 JSON 报告与 JSONL trace。
- 在 80-case seed benchmark 上完成五组 pipeline 初步消融，观察到 naive/hybrid Evidence Recall@5=1.0000 但 Precision@5=0.2924，GraphRAG Evidence Precision@5=0.8542，Planner Route Accuracy=0.6250，并定位 graph evidence mapping、planner routing、keyword metric 和 latency 等后续优化点。

## Version B: With Numbers

- 在 SupportOpsBench v2.4 80-case seed benchmark 上，对比 Dummy、Naive RAG、Hybrid RAG、GraphRAG 与 Agentic Planner，输出 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 和 latency 的可复现实验报告。

## v2.4 Resume Note

- Expanded SupportOpsBench from 20 to 80 seed cases with `seen/unseen/no_answer` splits and `easy/medium/hard` difficulty labels.
- Added benchmark quality tests for case count, continuous IDs, existing expected docs, task coverage, no-answer/security slices, multi-document cases, split coverage, and difficulty coverage.
- Re-ran five-pipeline ablation. On the 80-case seed benchmark: naive/hybrid Evidence Recall@5=1.0000, GraphRAG Evidence Recall@5=0.8646 and Precision@5=0.8542, Planner Evidence Recall@5=0.9625 and Route Accuracy=0.6250.
- Resume wording should still say "80-case seed benchmark" and should not claim production-level benchmark quality.

## Low-code Prototype Note

Added Dify/Coze-style workflow prototype documents to show how the SupportOps Agent flow can be visualized as low-code nodes. This is a prototype design artifact, not a production deployment.

## v2.3 Resume Note

- Added Evidence Precision@5 alongside Evidence Recall@5 to distinguish successful evidence recall from noisy retrieval.
- Treated Route Accuracy as planner/router-specific, reporting it as N/A for retrieval-only pipelines to avoid misleading comparisons.
- Updated the ablation report to compare retrieval quality, refusal behavior, routing behavior, and latency across dummy, naive RAG, hybrid RAG, GraphRAG, and planner pipelines.

# Risk Claims and Downgrades

| 危险表达 | 安全降级表达 |
| --- | --- |
| 构建企业级客服智能体系统 | 构建面向客服/运维工单场景的可复现 SupportOps Agent demo，并补充统一评测与消融分析 |
| 显著提升业务效率 | 在 20-case seed benchmark 上比较不同 pipeline 在 evidence recall、precision、route accuracy 和 latency 上的差异 |
| 生产级 GraphRAG 系统 | 实现 in-memory GraphRAG evidence pipeline，并用 Neo4j-style schema 记录图结构设计 |
| 基于 Neo4j 构建图数据库检索 | 设计 Neo4j-style schema，当前运行路径为 in-memory seed graph，Neo4j adapter 仍是 placeholder |
| Agent 自主规划复杂任务 | 实现 deterministic retrieval planner，根据 intent、skill 和 case_state 选择 evidence steps |
| 大规模 SupportOpsBench | 设计 20-case SupportOpsBench seed benchmark，作为评测 harness 和初步消融验证 |
| 证明系统可用于真实业务 | 通过本地 seed benchmark 和 trace/eval 验证核心工程路径，尚无线上业务证据 |
| GraphRAG 显著提升系统准确率 | 在 20-case seed benchmark 上，GraphRAG document-level Evidence Recall@5=0.95、Precision@5=0.9118 |
| Hybrid RAG 比 BM25 明显更强 | 在当前 seed benchmark 上 naive/hybrid Recall@5 均为 0.975；Hybrid 主要提供语义召回扩展位 |
| Planner 准确率达到 90% | Planner Route Accuracy=0.9 on 20-case seed benchmark；不代表答案准确率或生产指标 |
| 完整解决 RAG grounding | 实现 citation/evidence metrics，下一步补 citation precision 和 answer support checking |
| 完整安全防护 | 在 seed benchmark 中覆盖无答案拒答和安全边界，并通过 dry-run/verifier 降低写操作风险 |
| 完整 trace replay 系统 | 实现 trace recording 与 eval JSONL trace；完整 replay CLI 和断言仍需补证据 |
| 做了 leakage check | 已明确 dummy baseline 仅做 sanity check；完整 leakage audit 需补独立脚本和 holdout cases |
| 线上低延迟 Agent | 报告本地 eval latency summary；尚无 production SLA 或 repeated-run latency report |
| 自动完成退款/工单处理 | mock tools 支持 dry-run action proposal，不直接执行有副作用写操作 |
| 端到端客服机器人 | 当前是 CLI / local demo，重点在 retrieval、routing、tool safety、trace 和 eval 闭环 |
| 高分 dummy pipeline 证明能力 | dummy 是 rule-based sanity check，只验证 benchmark harness，不作为真实能力证据 |
| 完整 tool recall benchmark | 当前 tool recall 证据较轻，主要通过 planner/tool steps 和小 eval 验证，需补正式 tool recall cases |
| 已经上线企业客户 | 不能写；没有上线、客户、用户量、监控或业务指标证据 |


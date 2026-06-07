# Upgrade Plan

## 1 天

| 项目 | 做什么 | 为什么做 | 产出什么文件 | 简历可以多写什么 | 面试可以多讲什么 |
| --- | --- | --- | --- | --- | --- |
| README 项目结构更新 | 把当前 v2.3 模块、benchmark、报告路径和限制写清楚 | 面试官先看 README，结构不清会削弱可信度 | `README.md`, `docs/PROJECT_MEMORY.md` | “整理项目结构、评测入口与结果解释” | 能快速讲清模块边界和当前限制 |
| 录制 demo script | 写 3-5 条固定 CLI/demo query，覆盖 RAG、GraphRAG、planner、refusal | 防止面试时临场跑不稳定 | `scripts/demo.sh` 或 `docs/demo_script.md` | “提供可复现 demo script” | 能按固定路径演示 trace 和引用 |
| 整理 sample traces | 选 3 条代表性 trace：成功、多文档、拒答/安全 | trace 是 Agent 工程证据 | `docs/sample_traces.md`, `traces/samples/*.json` | “输出 sample trace 支持 failure diagnosis” | 能指着字段讲 router、citation、tool、verifier |
| 面试讲法复习 | 用本目录问答卡过一轮，压缩成 1 分钟和 3 分钟版本 | 防止把 seed benchmark 讲成生产系统 | `docs/job_materials/03_interview_story.md` | 不新增 claim | 能稳住真实性边界 |

## 3 天

| 项目 | 做什么 | 为什么做 | 产出什么文件 | 简历可以多写什么 | 面试可以多讲什么 |
| --- | --- | --- | --- | --- | --- |
| SupportOpsBench 20 → 80 cases | 扩 API Key、RAG 上传、权限、退款、登录、多文档、no-answer slices | 20 cases 指标波动大，最容易被质疑 | `evals/supportops_bench.yaml`, `reports/ablation_results.md` | “扩展到 80-case offline benchmark” | 能讲 task_type/split/difficulty 分层 |
| no-answer/security stress subset | 增加敏感信息、越权退款、知识库外问题、prompt injection 风格请求 | Refusal Accuracy 当前证据薄 | `evals/supportops_bench.yaml`, `reports/failure_cases.md` | “补充 refusal/security stress cases” | 能讲 refusal 的边界和失败样例 |
| citation precision 初版 | 统计 final answer citations 是否命中 expected_docs，区别 retrieval evidence 与 final citation | Evidence Recall 不能证明回答引用准确 | `evals/supportops_metrics.py`, `tests/test_supportops_eval.py`, `reports/ablation_results.md` | “新增 citation precision 初版” | 能解释 retrieval precision 与 citation precision |
| planner latency profiling | 分阶段记录 router/retriever/graph/tool/verifier/trace 耗时 | Planner latency 是当前明显风险 | `reports/planner_latency_profile.md`, `traces/latency_profile.jsonl` | “定位 planner latency 开销来源” | 能提出 early exit、缓存、超时降级 |

## 1 周

| 项目 | 做什么 | 为什么做 | 产出什么文件 | 简历可以多写什么 | 面试可以多讲什么 |
| --- | --- | --- | --- | --- | --- |
| answer support checking | 给 final answer 的关键 claim 匹配 citation/evidence，不满足则标 warning/refusal | 从 evidence retrieval 升级到 answer grounding | `app/verifier.py`, `evals/supportops_metrics.py`, `reports/answer_support_report.md` | “实现 answer support checking 初版” | 能讲 grounding 不是只看 top-k |
| graph source span mapping | 给 graph seed/node evidence 增加 `source_doc` / `source_span`，减少 query-signal mapping | 当前 GraphRAG mapping 证据仍偏规则 | `data/graph_seed.json`, `graph/`, `tests/test_supportops_eval.py` | “补充 graph evidence source_doc/source_span mapping” | 能回应 GraphRAG 是否作弊 |
| repeated-run latency report | 对五组 pipeline 跑多轮，报告 avg/p50/p95/max 和方差 | 单轮 20 cases latency 不稳定 | `reports/repeated_latency_report.md` | “补充 repeated-run latency report” | 能讲本地性能评估的局限 |
| JD 定制简历版本 | 针对 RAG Engineer、AI Agent Engineer、LLM App Backend 三类岗位写不同版本 | 不同 JD 关注点不同 | `docs/job_materials/jd_versions/*.md` | “按岗位突出 RAG/Agent/eval/后端工程” | 能把同一项目讲给不同面试官 |


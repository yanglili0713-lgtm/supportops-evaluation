# Interview Grilling

## RAG 基础

### 1. 你这个 RAG 的输入、chunk、索引和输出分别是什么？

- 面试官为什么会问：确认你不是只会说 RAG 名词。
- 危险回答：就是把文档丢给模型检索。
- 及格回答：输入是 `data/docs/*.md`，chunk 后用 BM25 返回 `doc_id/chunk_id/source/score/text`。
- 强回答：还能解释中文按字符、英文数字按词的 tokenizer，以及 citation 如何进入 trace/eval。

### 2. 为什么 BM25 在这个项目里仍然有价值？

- 面试官为什么会问：看你是否理解 keyword retrieval 的边界。
- 危险回答：BM25 比 embedding 更好。
- 及格回答：BM25 对错误码、API Key、权限词、文件名等精确信号稳定。
- 强回答：说明 BM25 召回 expected docs 稳定，但 Precision@5 低，不能只看 recall。

### 3. Evidence Recall@5 高说明什么，不说明什么？

- 面试官为什么会问：防止你把检索召回包装成答案正确。
- 危险回答：说明系统回答准确率很高。
- 及格回答：只说明 top5 里命中了 expected docs。
- 强回答：补充 Precision、citation precision、answer support checking 才能证明答案 grounding。

## Hybrid Retrieval

### 4. Hybrid RAG 比 naive RAG 改了什么？

- 面试官为什么会问：判断是不是堆技术。
- 危险回答：加了向量所以更智能。
- 及格回答：BM25 + 本地 token-vector，再做融合和 rerank。
- 强回答：承认当前 seed benchmark 上 Recall 与 naive 相同，价值主要是保留语义召回扩展位和可对比 baseline。

### 5. 你的 vector store 是真实 embedding 吗？

- 面试官为什么会问：识别夸大。
- 危险回答：是向量数据库能力。
- 及格回答：不是，是本地 token-vector fallback。
- 强回答：解释这是为了无 API key 可复现，不能写生产 embedding service。

### 6. Hybrid 的 Precision@5 为什么不高？

- 面试官为什么会问：看你是否会读坏指标。
- 危险回答：因为 benchmark 不准。
- 及格回答：top5 混入了额外相关但非 gold docs。
- 强回答：提出 citation precision、reranker、query intent slicing 和 expected evidence 标注扩展。

## GraphRAG

### 7. 你的 GraphRAG 到底是什么图？

- 面试官为什么会问：GraphRAG 很容易被过度包装。
- 危险回答：像 Neo4j 生产图谱一样。
- 及格回答：是 in-memory seed graph，包含用户、项目、上传任务、错误码、服务、工单、SOP。
- 强回答：说明 `schema.cypher` 是 Neo4j-style schema 文档，`neo4j_adapter.py` 是 placeholder。

### 8. GraphRAG Evidence Recall@5 从早期低值到 0.95，是不是作弊？

- 面试官为什么会问：指标提升太大。
- 危险回答：GraphRAG 更强所以暴涨。
- 及格回答：不是模型能力暴涨，是把 graph evidence 映射到 document-level expected_docs。
- 强回答：说明映射规则、测试、限制，并承认还没有 source_span。

### 9. GraphRAG keyword hit 为什么是 0？

- 面试官为什么会问：结果表里有明显异常。
- 危险回答：keyword metric 没意义。
- 及格回答：GraphRAG 输出 path summary，不是面向 expected_keywords 的自然语言答案。
- 强回答：区分 evidence retrieval metric 与 answer quality metric，提出 semantic judge 或 answer generator。

## Agentic Planner

### 10. Planner 是 LLM planner 吗？

- 面试官为什么会问：防止你把规则 planner 写成 agentic intelligence。
- 危险回答：是 Agent 自主规划。
- 及格回答：不是，是 deterministic local planner。
- 强回答：解释它根据 intent、skill、case_state 选择 bm25/vector/graph/tools/escalate steps，可测试、可复现。

### 11. Planner Route Accuracy=0.9 代表什么？

- 面试官为什么会问：确认 metric 适用范围。
- 危险回答：代表整个 agent 准确率 90%。
- 及格回答：代表 20-case seed benchmark 上 predicted route 与 expected_route 的匹配。
- 强回答：强调只适用于 planner/router pipeline，不代表答案正确或生产质量。

### 12. Planner 为什么 latency 更高？

- 面试官为什么会问：看你会不会分析系统开销。
- 危险回答：因为更高级。
- 及格回答：它多跑 router、memory、skill、hybrid retrieval、graph/tool、verifier、trace。
- 强回答：能提出缓存、early exit、timeout、route confidence threshold、异步工具调用。

## Evaluation

### 13. 为什么 benchmark 只有 20 条？

- 面试官为什么会问：评估可信度。
- 危险回答：20 条已经够了。
- 及格回答：它是 seed benchmark，用来验证 harness 和做初步消融。
- 强回答：说明下一步扩到 80-120 cases，并按 task_type/split/difficulty 切片。

### 14. dummy pipeline 高分说明什么？

- 面试官为什么会问：看你是否误读 baseline。
- 危险回答：说明系统能力很强。
- 及格回答：只说明评测 harness 能跑通。
- 强回答：dummy 是 rule-aligned sanity check，不能作为真实 agent 能力。

### 15. 五组 pipeline 消融怎么保证公平？

- 面试官为什么会问：检查实验设计。
- 危险回答：都跑同一套就是公平。
- 及格回答：同一 20-case benchmark，同一指标入口。
- 强回答：补充 route metric pipeline-aware，GraphRAG 做 document mapping，仍需扩集和 human review。

## Metrics

### 16. Evidence Precision@5 为什么重要？

- 面试官为什么会问：看你是否理解 noisy retrieval。
- 危险回答：precision 越高答案越好。
- 及格回答：它衡量 top5 中 expected docs 的占比。
- 强回答：说明 naive/hybrid recall 高但 precision 低，暴露召回噪声。

### 17. Refusal Accuracy 是怎么定义的？

- 面试官为什么会问：安全指标容易虚。
- 危险回答：模型自己会拒绝。
- 及格回答：根据 `should_refuse` 和 refusal markers 判断。
- 强回答：承认是规则式 seed metric，需要 stress subset 和人工审查。

### 18. latency 怎么测的？

- 面试官为什么会问：本地 latency 可能不稳定。
- 危险回答：表里数字就是性能。
- 及格回答：`time.perf_counter()` 包一条 case 的 pipeline run。
- 强回答：说明当前是本地 eval latency，不能写 SLA，需要 repeated-run report。

## Leakage Check

### 19. 你做了 leakage check 吗？

- 面试官为什么会问：20-case seed 容易被规则对齐。
- 危险回答：做了完整数据泄漏检测。
- 及格回答：目前主要是明确 dummy rule baseline 不作为能力证据。
- 强回答：说“谨慎写”，下一步补 train/dev/test 分离、rule overlap audit、case paraphrase holdout。

### 20. dummy 和真实 pipeline 共享了哪些先验？

- 面试官为什么会问：检查 benchmark 污染。
- 危险回答：没有影响。
- 及格回答：dummy 显式按 query keywords 路由和返回 docs。
- 强回答：把 dummy 定位为 harness sanity check，真实结论来自 naive/hybrid/graph/planner 对比。

## Trace Replay

### 21. trace replay 现在做到什么程度？

- 面试官为什么会问：trace recording 和 replay 不一样。
- 危险回答：完整 replay。
- 及格回答：目前有 trace recording 和 eval JSONL trace。
- 强回答：谨慎写 trace recording；replay 需要补固定输入、固定输出校验和 replay CLI。

### 22. trace 里保存哪些字段？

- 面试官为什么会问：看可观测性是否真实。
- 危险回答：保存日志。
- 及格回答：router、skill、case_state、citations、graph evidence、tool calls、warnings、final answer。
- 强回答：说明这些字段可用于定位 RAG、router、tool、verifier 的失败归因。

## Refusal / Safety

### 23. 你怎么防止直接执行退款或创建工单？

- 面试官为什么会问：写操作安全是 Agent 关键风险。
- 危险回答：提示词要求不要执行。
- 及格回答：mock write tools 默认 `dry_run=True`。
- 强回答：verifier 会检查 write tool dry_run，并把 proposal 与真正执行分开。

### 24. 无答案问题怎么处理？

- 面试官为什么会问：RAG 幻觉风险。
- 危险回答：模型会说不知道。
- 及格回答：benchmark 有 no-answer cases，answer 没证据时返回没有足够证据。
- 强回答：后续补 answer support checking，要求 final answer 每个 claim 对应 citation。

## Latency

### 25. Planner latency 高会不会不能用？

- 面试官为什么会问：工程取舍。
- 危险回答：高一点没关系。
- 及格回答：当前只是本地 demo latency，说明 planner 有额外开销。
- 强回答：提出按 intent 早退、缓存 graph/retriever、工具并发、超时降级。

### 26. p95 latency 在 20 cases 上可靠吗？

- 面试官为什么会问：小样本统计风险。
- 危险回答：可靠。
- 及格回答：不可靠，只是初步信号。
- 强回答：需要 repeated-run latency report 和更多 cases。

## Engineering Reliability

### 27. 这个项目最工程化的部分是什么？

- 面试官为什么会问：区分 demo 和工程实践。
- 危险回答：用了很多技术。
- 及格回答：模块可测试、trace、eval、failure report。
- 强回答：强调把失败模式变成可复现评测，而不是只改 prompt。

### 28. 哪些模块还不成熟？

- 面试官为什么会问：看你是否诚实。
- 危险回答：基本都成熟。
- 及格回答：benchmark 小、GraphRAG 无 source_span、planner 是规则式、refusal cases 少。
- 强回答：给出 1天/3天/1周补证据计划。

## Resume Risk

### 29. 能不能写企业级？

- 面试官为什么会问：看你是否过度包装。
- 危险回答：可以，场景是企业客服。
- 及格回答：不能写生产级企业系统。
- 强回答：写“面向企业客服/运维约束的可复现 Agent demo 与 seed benchmark”。

### 30. 能不能写显著提升业务效率？

- 面试官为什么会问：结果影响需要业务证据。
- 危险回答：可以，因为指标提升。
- 及格回答：不能，没有线上业务效率数据。
- 强回答：只能写 seed benchmark 上不同 pipeline 的 evidence、route、refusal、latency 差异。


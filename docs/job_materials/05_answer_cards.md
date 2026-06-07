# Answer Cards

## 1. 为什么要做多个 RAG，不是堆技术吗？

### 30 秒短答

不是为了堆名词。我把 naive、hybrid、graph、planner 放在同一 benchmark 下，是为了比较不同证据获取方式在 recall、precision、route 和 latency 上的行为差异。

### 2 分钟展开

naive BM25 对错误码和关键词稳定；Hybrid 保留语义召回扩展位；GraphRAG 用结构化路径补充用户、服务、工单和错误码上下文；Planner 根据 intent、skill 和 case_state 选择证据步骤。当前 20-case seed benchmark 显示 naive/hybrid Recall@5 高但 Precision@5 低，GraphRAG Precision@5 更高，Planner 有 route 能力但 latency 更高。所以我不会说哪个绝对更好，而是把它们作为可复现实验对象。

### 一句总结

多个 pipeline 的价值是可对比、可消融、可定位失败，不是简历堆技术。

## 2. GraphRAG Evidence Recall@5 从 0.15 到 0.95，是不是作弊？

### 30 秒短答

不是能力暴涨，而是修正了评测空间不一致：graph evidence 是路径，benchmark expected evidence 是文档路径。

### 2 分钟展开

早期 GraphRAG 可以返回用户、错误码、服务、工单路径，但这些路径没有稳定映射到 `data/docs/*.md`，所以 Evidence Recall 被低估。后来我在 adapter 里用 graph evidence、linked entities 和 query signals 做保守 document mapping，并加了测试覆盖 EMBEDDING_FAILED 和 API Key 问题。这个结果只能写成 seed benchmark 上的 evidence mapping 改进，不能写成 GraphRAG 生产能力。

### 一句总结

这是 evidence-to-document mapping 修正，不是模型或图谱能力的夸张提升。

## 3. Evidence Recall@5 和 Evidence Precision@5 有什么区别？

### 30 秒短答

Recall 看 expected docs 有没有进 top5，Precision 看 top5 里有多少是 expected docs。

### 2 分钟展开

如果 expected docs 是 1 篇，top5 里命中了它，Recall@5 就是 1。但如果 top5 同时混入 4 篇无关文档，Precision@5 只有 0.2。这个项目里 naive/hybrid Recall@5=0.975，但 Precision@5=0.2971，说明召回稳定但证据噪声较大。

### 一句总结

Recall 防漏召，Precision 防 top-k 证据太脏。

## 4. 为什么 naive/hybrid 的 route accuracy 是 N/A？

### 30 秒短答

因为 naive 和 hybrid 是检索 pipeline，不负责业务路由。

### 2 分钟展开

Route Accuracy 比较 predicted route 和 expected_route。naive/hybrid/graph 返回的是检索结果，不应该被要求输出 `api_key_issue`、`billing_refund` 这类业务 intent。v2.3 里我把 route metric 改成 pipeline-aware，只对 dummy 和 planner 报告 route accuracy，对 retrieval-only pipeline 标成 N/A。

### 一句总结

不能用路由指标惩罚不做路由的检索系统。

## 5. 为什么 GraphRAG keyword hit 是 0？

### 30 秒短答

GraphRAG 当前输出 graph path summary，不是面向 expected keywords 优化的自然语言答案。

### 2 分钟展开

Keyword Hit Rate 是轻量 surface metric。GraphRAG 的答案格式类似“GraphRAG found paths”，它能映射到 expected docs，但不一定包含 benchmark 里的关键词。因此 keyword hit 低不等于 graph evidence 错。这个 failure case 已记录，下一步应加 answer generation、semantic judge 或 human review。

### 一句总结

GraphRAG 当前强在 evidence path，不强在关键词式答案表达。

## 6. Planner 为什么 latency 更高？

### 30 秒短答

Planner 多做了 routing、memory、skill selection、retrieval planning、tools、verifier 和 trace。

### 2 分钟展开

naive/hybrid 基本只检索；planner 会先路由，更新 case_state，选 skill，规划 bm25/vector/graph/tool/escalate steps，再运行 verifier 和 trace recording。所以它的 avg/p95 latency 更高。这个结果不能写成 SLA，只能写成本地 seed eval 的开销对比。

### 一句总结

Planner latency 高是功能路径更长，后续需要缓存、early exit 和 repeated-run profiling。

## 7. 你怎么防止无答案时模型编造？

### 30 秒短答

当前做法是 no-answer/security cases、refusal markers、verifier 和 citation 检查。

### 2 分钟展开

SupportOpsBench 里有 no-answer 和 security boundary cases，比如要求真实 API Key、绕过退款审核、知识库没有的办公室空调问题。metrics 用 `should_refuse` 和 refusal markers 计算 Refusal Accuracy。agent loop 中 verifier 检查 citations、graph evidence、tool calls 是否缺失，缺失时 next_action 是 retry 或保守回答。局限是规则式，还需要更多 adversarial cases 和 answer support checking。

### 一句总结

目前能做 seed-level refusal regression，但还不能声称完整安全防护。

## 8. 你这个 benchmark 只有 20 条，能说明什么？

### 30 秒短答

只能说明评测 harness 和初步消融结果，不能说明生产效果。

### 2 分钟展开

20 cases 覆盖了 API Key、RAG 上传、退款、权限、登录、多文档、no-answer 和安全边界，适合验证指标定义、pipeline adapter、trace 输出和 failure analysis。它的价值是把 demo 变成可重复评测，但样本太小，指标会受少数 case 影响。简历里必须写 20-case seed benchmark。

### 一句总结

它是 seed benchmark，不是大规模能力证明。

## 9. 你的项目和 Dify/low-code 有什么区别？

### 30 秒短答

这个项目重点是 Python 工程实现、可测试模块、trace/eval/failure analysis，而不是低代码编排。

### 2 分钟展开

Dify/Coze 更适合快速搭 workflow。我这个项目把 router、memory、retriever、planner、verifier、mock tools 和 eval 都拆成代码模块，能写单元测试、做消融、输出 JSON/JSONL trace、分析 route metric 适用性和 evidence precision。这更适合展示 Agent 工程问题的定位和评测闭环。

### 一句总结

低代码强调搭流程，这个项目强调可复现工程实现和评测归因。

## 10. 这个项目下一步怎么做？

### 30 秒短答

优先补证据：扩 benchmark、补 no-answer/security stress、citation precision、planner latency profiling。

### 2 分钟展开

1 天内先整理 README、sample traces 和 demo script；3 天内把 SupportOpsBench 从 20 扩到 80 cases，增加 refusal/security subset 和 citation precision；1 周内做 answer support checking、graph source_span mapping、repeated-run latency report，并按目标 JD 定制简历版本。这样可以把“可复现 demo”升级到“更可信的离线评测项目”。

### 一句总结

下一步不是加名词，而是把证据链补厚。


# Final Interview Playbook

## 1-minute Project Pitch

我做的是一个面向客服/运维工单场景的 SupportOps Agent 本地工程 demo。它不是单次聊天 demo，而是围绕 Agent 工程里常见失败点来做：RAG 召回不稳、router 高置信但选错、多轮 case 信息丢失、工具调用和写操作需要 dry-run、回答需要 evidence 和 trace。

系统包含 intent router、case-state memory、SOP skills、mock tools、BM25 RAG、Hybrid Retrieval、in-memory GraphRAG、deterministic planner、verifier 和 trace output。为了避免只展示一个 query，我设计了 SupportOpsBench v2.4 80-case seed benchmark，对 dummy、naive、hybrid、graph、planner 五组 pipeline 做消融，报告 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 和本地 latency。所有结论都限定在 seed benchmark 和本地 demo 范围内。

## 3-minute Project Pitch

客服和运维工单不是普通 FAQ。一个问题可能同时涉及错误码、用户权限、上传任务、账单、日志、SOP 和安全边界。只做普通 RAG 容易出现“检索到了但证据很脏”“没证据却回答”“路由错 skill”“多轮里 user_id/error_code 丢失”等问题。

我把项目拆成可测试模块：router 输出 intent/confidence/reason/matched keywords；memory 维护 `CaseState`；skills 用 `SKILL.md` 固化 API key、登录、退款、RAG 上传和 escalation SOP；mock tools 模拟用户、账单、日志、工单系统，写操作默认 dry-run；RAG 返回 citation；GraphRAG 用 in-memory seed graph 返回用户、项目、错误码、服务、工单等路径证据；planner 根据 intent、skill 和 case_state 选择检索、图证据和 mock tool；verifier 检查 evidence 和 dry-run；trace 保存一次运行过程。

评测方面，我扩展了 SupportOpsBench 到 80 个 seed cases，覆盖 11 类任务、seen/unseen/no_answer split、easy/medium/hard 难度、27 个 multi-doc case 和 12 个 no-answer/security refusal case。五组 pipeline 结果显示：naive/hybrid Recall@5=1.0000 但 Precision@5=0.2924，说明召回不等于干净证据；GraphRAG Precision@5=0.8542 但 Recall@5=0.8646，说明结构化证据更集中但覆盖有限；Planner Evidence Recall@5=0.9625，Route Accuracy=0.6250，暴露了 deterministic routing 在混合症状和改写表达上的不足。

我会把这个项目讲成可复现 demo + seed benchmark + failure analysis，不讲生产上线、不讲大规模图谱，也不把 dummy baseline 的高分当成能力证明。

## Deep-dive Q&A

### 1. 为什么要做多个 RAG？是不是堆技术？

短答：不是堆技术，而是把不同证据获取方式放进同一 benchmark 下比较 recall、precision、route、latency 和 failure mode。

强回答：BM25 对错误码、API Key、权限词稳定；Hybrid 提供语义召回扩展位；GraphRAG 用结构化路径补用户、项目、服务、工单和错误码上下文；Planner 负责根据 intent/skill/case_state 选择证据步骤。v2.4 结果里 naive/hybrid Recall@5 高但 Precision@5 低，GraphRAG Precision 高但 Recall 低，Planner route 暴露错误路由，这说明多个 pipeline 的价值是消融和定位问题。

不能说的话：用了多个 RAG 所以系统更先进；GraphRAG 一定比普通 RAG 强。

### 2. 数据量不大，为什么不用 Milvus / Neo4j？

短答：当前是本地 seed benchmark 和小规模 demo，用 Markdown、BM25、本地 token-vector 和 in-memory graph 更匹配。

强回答：项目目标是验证 Agent 工程闭环和评测指标，不是搭重型基础设施。Milvus/Neo4j 在生产和大规模数据上有价值，但这里没有数据规模、部署、运维和在线查询压力证据。仓库里有 Neo4j-style schema 和 optional adapter placeholder，但实际 eval 用的是 in-memory graph。

不能说的话：我用了 Milvus/Neo4j；这是大规模知识图谱。

### 3. GraphRAG 的价值是什么？

短答：GraphRAG 用结构化关系补充文档检索，比如 user/team/project/upload job/error code/service/ticket/skill 的路径证据。

强回答：普通 RAG 直接从 docs 召回，适合政策和排查文档；GraphRAG 更适合表达“哪个用户属于哪个 team、哪个 upload job 失败、错误码由哪个 service 抛出、关联哪个 ticket 或 skill”。在本项目中它不是生产图谱，而是 in-memory seed graph，用于验证结构化证据和文档 evidence mapping。

不能说的话：GraphRAG 自动做根因分析；GraphRAG 已接入真实企业图数据库。

### 4. GraphRAG 为什么 recall 低于 naive/hybrid，但 precision 高？

短答：GraphRAG 的映射更保守，命中时 evidence 更集中，但对改写、混合症状和缺少显式实体的 case 覆盖不足。

强回答：naive/hybrid 会返回 top5 文档，expected doc 容易进 top5，所以 Recall@5=1.0000，但也混入额外文档，Precision@5=0.2924。GraphRAG 依赖 graph path、linked entities、query signals 映射到 docs，返回更少且更集中的 evidence，所以 Precision@5=0.8542；但 graph nodes 还没有完整 source_doc/source_span，遇到 paraphrase 或弱信号会漏，Recall@5=0.8646。

不能说的话：GraphRAG recall 低是 benchmark 不公平；precision 高代表答案一定正确。

### 5. Evidence Recall@5 和 Evidence Precision@5 区别？

短答：Recall 看 expected docs 有没有进 top5；Precision 看 top5 里有多少是 expected docs。

强回答：如果 expected doc 只有 1 篇，top5 命中了它，Recall@5 就是 1.0；但如果另外 4 篇都是噪声，Precision@5 就是 0.2。这个项目里 naive/hybrid 高 recall 但低 precision，说明只看 recall 会掩盖 noisy retrieval。

不能说的话：Evidence Recall@5 高就代表回答准确。

### 6. Planner Route Accuracy 0.625 怎么解释？

短答：它说明 deterministic router/planner 在 80-case seed benchmark 上只正确匹配了 62.5% 的 expected route，不代表整体答案准确率。

强回答：v2.4 扩展了 paraphrase、multi-symptom、no-answer 和 security boundary cases，router/planner 仍是规则和本地确定性逻辑，所以 Route Accuracy 从小样本结果下降是合理暴露问题。这个指标只对 planner/router pipeline 有意义，naive/hybrid/graph 标为 N/A。

不能说的话：Planner 准确率 62.5% 说明系统整体能力是 62.5%；或者把它包装成高准确率。

### 7. 你怎么防止 benchmark leakage？

短答：目前只能谨慎处理，不能声称完整 leakage audit；我明确把 dummy 定位为 rule-aligned harness sanity check，不把它的高分当能力。

强回答：SupportOpsBench 是 seed benchmark，真实风险是规则和 case wording 过近。当前缓解包括 seen/unseen/no_answer split、difficulty 标签、dummy 与真实 pipeline 分开解读、route metric pipeline-aware、expected_docs 必须来自真实 docs。下一步应做 rule overlap audit、paraphrase holdout、独立 dev/test 和 human review。

不能说的话：已经完成严格防泄漏评估。

### 8. 你怎么处理无答案和安全边界？

短答：benchmark 有 no-answer/security cases，metric 用 `should_refuse` 和 refusal markers；mock 写操作默认 dry-run，verifier 检查 evidence 和 write safety。

强回答：项目覆盖真实 token/API key 请求、绕过退款审核、知识库没有答案等 case。当前 Refusal Accuracy 是 seed-level 规则式指标，v2.4 real pipelines 大约 0.85。它能做回归，但不能代表完整安全评测；后续需要更多 adversarial cases 和 answer-support checking。

不能说的话：系统已经具备完整安全防护。

### 9. Dify/Coze 原型到底完成到什么程度？

短答：完成的是 Dify/Coze-style workflow prototype design artifacts，不是官方导出，不是生产部署。

强回答：仓库新增了 `docs/lowcode_workflow_prototype.md` 和两个 workflow prototype JSON，说明 SupportOps flow 如何拆成 input、router、knowledge retrieval、graph lookup、mock tool、condition、answer/refusal、trace 节点。它用于展示可视化编排思路，主实现仍是 Python。

不能说的话：完成 Dify/Coze 生产级部署；上线了低代码客服机器人。

### 10. 这个项目离生产级还差什么？

短答：差真实数据、权限体系、线上工具集成、人工审核、监控告警、完整安全评测、稳定 SLA 和更大 benchmark。

强回答：当前是本地可复现 demo。生产化至少需要真实企业数据接入和脱敏、认证授权、工具写操作审批、审计日志、在线/离线评测闭环、citation/answer support checking、更多 no-answer/security stress cases、错误恢复、重试/超时、监控、部署和人工回退流程。

不能说的话：已经接近生产可用；可以直接给企业客服上线。

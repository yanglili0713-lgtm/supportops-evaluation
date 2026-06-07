# Interview Story

## 1-minute version

我做的是一个面向客服和运维工单场景的 SupportOps Agent 工程 demo。它不是普通聊天机器人，而是围绕真实 Agent 容易出问题的地方来做：RAG 召回不稳、路由高置信但选错、case 信息在多轮里丢失、工具调用和写操作需要 trace 与 dry-run。

系统里有 BM25 RAG、Hybrid Retrieval、in-memory GraphRAG、deterministic planner、SOP skill、mock tools、verifier 和 trace。为了避免只展示一个 demo query，我设计了 20-case SupportOpsBench seed benchmark，对 dummy、naive、hybrid、graph、planner 五组 pipeline 做消融，报告 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 和 latency。当前结果只能说明 seed benchmark 上的初步行为，不写成生产结论。

## 3-minute version

### 背景问题

客服/技术支持场景的问题通常不是单纯问答。用户可能问 API Key 失效、RAG 上传后搜不到、退款审核、权限不足、登录态过期，系统需要结合知识库、错误码、用户状态、账单、日志、SOP 和安全边界。

### 系统设计

我把系统拆成几个可测试模块：Router 识别 intent，Memory 保存结构化 case_state，Skill 约束 SOP，RAG/Hybrid RAG 做文档检索，GraphRAG 从 seed graph 找用户、错误码、服务和工单路径，Planner 根据 intent、skill 和 case_state 选择证据步骤，Verifier 检查 citation、graph evidence、tool calls 和 dry-run，TraceRecorder 保存一次运行过程。

### 评测集设计

我设计了 SupportOpsBench seed benchmark，目前是 20 cases，覆盖 FAQ、API Key、credential/token、权限、登录、退款、RAG 上传、incident diagnosis、多文档诊断、无答案拒答和安全边界。它的定位是验证评测框架和做初步消融，不是大规模 benchmark。

### 指标设计

指标包括 Keyword Hit Rate、Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 和 latency。后来我把 Route Accuracy 改成 pipeline-aware：只有 dummy 和 planner 这种有 route 决策的 pipeline 才报告，naive/hybrid/graph 标为 N/A，避免把检索系统误判成路由失败。

### 关键优化：GraphRAG evidence mapping

一个关键问题是 graph path evidence 和 benchmark expected_docs 不在同一空间。早期 GraphRAG 找到了图路径，但不能稳定映射到 `data/docs/*.md`，Evidence Recall 会被低估。我在 adapter 里把 graph evidence、linked entities 和 query signals 保守映射到真实文档路径，并加测试覆盖 EMBEDDING_FAILED、API Key 等案例。这个优化后，20-case seed benchmark 上 GraphRAG Evidence Recall@5=0.95，Precision@5=0.9118。

### 结果

在 20-case seed benchmark 上，naive/hybrid Evidence Recall@5=0.975，但 Precision@5=0.2971，说明能召回 expected docs 但 top-k 比较 noisy。GraphRAG Recall@5=0.95、Precision@5=0.9118。Planner Route Accuracy=0.9，但 latency 更高，因为它执行 routing、planning、tool selection、verification 和 trace recording。

### 局限与下一步

局限是 benchmark 只有 20 cases，GraphRAG 是 in-memory seed graph，planner 是 deterministic local planner，dummy 高分只是 harness sanity check。下一步是扩展到 80-120 cases，补 no-answer/security stress subset、citation precision、answer support checking、graph source_span mapping 和 repeated-run latency report。

## STAR version

### Situation

客服/运维 Agent 很容易在真实工程问题上失败：RAG 找不到证据、路由选错 skill、多轮 case 信息丢失、工具调用缺 trace、写操作越权、无答案时编造。

### Task

我的目标是构建一个可复现的 SupportOps Agent demo，并用统一 seed benchmark 证明不同 pipeline 的行为差异，而不是只做单次 demo。

### Action

我实现了 BM25 RAG、Hybrid Retrieval、in-memory GraphRAG、deterministic Planner、SOP skill、mock tools、verifier 和 trace recording；设计 20-case SupportOpsBench；实现 Evidence Recall@5、Evidence Precision@5、Refusal Accuracy、Route Accuracy 与 latency；并补充 ablation report 和 failure analysis。

### Result

在 20-case seed benchmark 上，naive/hybrid Recall@5=0.975，GraphRAG Recall@5=0.95、Precision@5=0.9118，Planner Route Accuracy=0.9。更重要的是，我把结果限定为 seed benchmark 初步证据，同时明确了 dummy 高分、GraphRAG source span、planner latency、no-answer stress cases 等后续补证据方向。


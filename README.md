# SupportOps Agent：面向企业支持场景的 RAG + MCP + Skills Agent 工程项目

SupportOps Agent 是一个面向企业客服与技术支持场景的 Agent 工程项目。

项目目标不是做一个普通聊天机器人，而是构建一个具备真实工程约束的企业支持 Agent，用于实践：

- RAG 知识库检索
- Intent Router 意图路由
- Case State 多轮记忆
- MCP Mock Tools 外部系统工具调用
- Skills 企业 SOP 流程约束
- Trace 可观测性
- Eval 失败模式评估
- Hybrid RAG 融合检索

项目刻意围绕真实 Agent 工程问题设计，例如：

- RAG 中文查询召回失败如何定位；
- 工具调用没有正确召回怎么发现；
- Router 高置信度但路由错误怎么处理；
- 多轮对话中用户关键信息丢失怎么办；
- 写操作工具如何避免模型直接执行；
- Agent 回答错了如何通过 trace 和 eval 定位问题。

---

## 1. 项目背景

企业客服和技术支持场景中，用户问题往往不能只靠知识库回答，还需要结合：

- 产品 FAQ；
- 退款政策；
- API Key 指南；
- RAG 上传失败排查文档；
- 用户资料；
- 账单信息；
- 日志信息；
- 工单系统；
- 企业 SOP 流程。

普通 RAG 问答只能解决“查文档”，但不能完成完整业务流程。普通工具调用 Agent 又容易出现工具召回错误、长对话状态丢失、错误路由和越权写操作等问题。

因此，本项目将 RAG、Router、Memory、MCP Mock Tools、Skills、Trace 和 Eval 串成一个小型但真实约束明确的 Agent 工程系统。

---

## 2. 系统架构

整体流程：

```text
用户问题
  ↓
Intent Router
  ↓
Case State Memory
  ↓
Skill Selector
  ↓
RAG Retriever
  ↓
MCP Mock Tools
  ↓
Trace Recorder
  ↓
Eval / Report
模块分工：

rag/
  负责文档加载、chunking、BM25 检索和 citation 返回。

app/router.py
  负责识别用户意图，输出 intent、confidence、reason、matched_keywords。

app/memory.py
  负责维护结构化 case_state，避免多轮对话丢失 user_id、plan、error_code 等信息。

mcp_servers/
  模拟企业外部系统，包括用户、账单、工单和日志工具。

skills/
  保存企业 SOP，例如退款处理、登录排查、API Key 恢复、RAG 上传失败排查。

app/tracing.py
  记录一次 Agent 运行过程，包括路由、记忆、引用、工具调用和最终答案。

evals/
  评估 Router、Memory、RAG grounding 和高置信错误路由等失败模式。
Phase 7：Hybrid RAG

实现内容：

新增 SimpleVectorStore、HybridRetriever 和轻量 reranker；
不依赖真实 embedding API，默认使用本地 token vector + cosine similarity；
支持 BM25 + Vector 融合检索，并保留 doc_id、chunk_id、source citation；
新增 hybrid_rag_eval 并集成到 evals/run_all.py。

真实问题：

BM25 命中关键词稳定，但面对“文档导入后答案没有依据”这类近义表达时召回不足；纯向量检索又可能让 citation 稳定性变差。

解决方式：

用 Hybrid RAG 让 BM25 负责精确和 citation 稳定性，vector search 补足语义召回，并用 reranker 做轻量重排。

挑战记录：

docs/challenges/phase7_hybrid_rag_issue.md
3. 已完成阶段
Phase 1：RAG MVP

实现内容：

从 data/docs/*.md 加载知识库；
对文档进行 chunking；
使用 BM25 检索；
返回 citation；
支持 CLI 查询；
保存运行 trace。

真实问题：

单元测试通过，但真实中文查询“上传PDF后检索不到内容怎么办？”无法召回文档。

解决方式：

将 tokenizer 改为中英文混合策略；
英文和数字按词切分；
中文按字符切分；
补充 no-space 中文查询回归测试。

挑战记录：

docs/challenges/phase1_chinese_recall_issue.md
Phase 2：Intent Router

实现内容：

支持 login_issue、billing_refund、api_key_issue、rag_upload_issue、permission_issue、deployment_error、general_faq、unknown；
输出 intent、confidence、reason、matched_keywords；
构建 data/gold_cases.jsonl；
使用测试约束高风险路由样例。

真实问题：

“上传 PDF 后检索不到内容”可能被错误路由到 permission_issue。

解决方式：

Router 输出 matched_keywords 和 reason；
构造 gold cases；
增加高风险样例测试；
将错误路由变成可测试、可回归的问题。

挑战记录：

docs/challenges/phase2_router_confidence_issue.md
Phase 3：Case State Memory

实现内容：

实现结构化 case_state；
抽取 user_id、plan、intent、error_code、invoice_id、uploaded_file_type、attempted_steps、missing_info；
支持多轮对话状态更新；
添加 memory regression tests。

真实问题：

长对话里用户第一轮提供的 user_id、plan、error_code 后续容易丢失。

解决方式：

不依赖完整聊天历史；
把自然语言对话压缩为结构化 case_state；
每轮更新并回归测试。

挑战记录：

docs/challenges/phase3_memory_loss_issue.md
Phase 4：MCP Mock Tools

实现内容：

user_server.py：查询用户资料、套餐、权限；
billing_server.py：查询账单、退款状态、创建退款申请；
ticket_server.py：创建和查询工单；
logs_server.py：查询错误日志；
所有工具返回结构化 dict；
写操作默认 dry-run。

真实问题：

Agent 不能直接执行退款、创建工单这类有副作用的写操作。

解决方式：

写操作默认 dry_run=True；
只返回 action proposal；
将“模型想做什么”和“系统真正执行什么”分离。

挑战记录：

docs/challenges/phase4_tool_write_safety_issue.md
Phase 5：Skills SOP

实现内容：

创建 refund_policy、login_troubleshooting、api_key_recovery、rag_upload_debug、escalation 等 Skills；
每个 Skill 包含适用场景、必须收集的信息、可用 RAG 文档、可用 MCP Tools、禁止事项、处理步骤、升级人工条件和输出模板；
实现 skill_loader 和 skill_selector。

真实问题：

Router 只能判断意图，不能保证 Agent 按企业业务流程处理。

解决方式：

用 Skills 显式沉淀企业 SOP；
让 Agent 从“能路由问题”升级为“按流程处理问题”。

挑战记录：

docs/challenges/phase5_skill_sop_issue.md
Phase 6：Trace and Eval

实现内容：

实现 TraceRecorder；
保存 user_message、router_result、selected_skill、case_state、retrieved_citations、tool_calls、final_answer 和 warnings；
实现 tool_recall_eval、router_confusion_eval、memory_regression_eval、rag_grounding_eval；
汇总生成 evals/report.md。

真实问题：

Agent 回答错了以后，如果没有 trace 和 eval，很难判断是 RAG、Router、Memory、Tool 还是 Skill 出问题。

解决方式：

保存完整运行 trace；
构建多个 eval 脚本；
把失败模式变成可复现的工程指标。

挑战记录：

docs/challenges/phase6_trace_eval_observability_issue.md
4. 当前测试结果

运行：

uv run pytest -q

当前测试结果：

44 passed

运行评估：

uv run python -m evals.run_all

当前 eval 结果包括：

Router accuracy：1.0
high_confidence_wrong_route：[]
memory_regression：passed
rag_grounding：passed
hybrid_rag：passed
graphrag：passed

Phase 8：GraphRAG

实现内容：

新增 Neo4j 风格 `graph/schema.cypher`、`data/graph_seed.json`、in-memory graph builder、entity linker、graph retriever 和可选 Neo4j adapter；
支持从 `user_id` 查 team/project/upload_job；
支持从 `error_code` 查 service、historical ticket 和相关 skill；
支持 service dependency 查询。

真实问题：

普通 RAG 能查文档，但无法回答“哪个用户的哪个项目、哪个上传任务、哪个服务和哪个历史工单有关”。

解决方式：

用 GraphRAG 补充 user/project/error/service/ticket 关系链；测试默认使用 in-memory graph，生产可替换 Neo4j。

挑战记录：

docs/challenges/phase8_graphrag_issue.md
5. 快速运行
5.1 安装依赖
uv venv --python 3.12
uv pip install -e ".[dev]"
5.2 运行测试
uv run pytest -q
5.3 运行 RAG CLI
printf '上传PDF后检索不到内容怎么办？\n' | uv run python -m app.cli
5.4 运行 Eval
uv run python -m evals.run_all
6. 项目亮点
不是简单套壳聊天机器人，而是围绕企业支持场景设计的 Agent 工程项目；
覆盖 RAG、Router、Memory、MCP Mock Tools、Skills、Trace、Eval；
每个阶段都记录真实问题与解决方案；
通过 pytest 和 eval 脚本保证结果可回归；
强调工具调用安全、长对话状态管理、路由可解释性和 RAG grounding；
适合展示 Agent 工程能力，而不只是 Prompt/API 调用能力。
7. 当前局限性
当前 MCP 仍是本地 mock tool，没有接入真实 MCP 网络协议；
Router 基于规则和关键词，没有接入 LLM 或 embedding 语义路由；
RAG 当前使用 BM25，没有加入 embedding hybrid retrieval 和 rerank；
Skills 当前是 Markdown SOP，还没有接入完整 Agent 执行器；
Trace 和 Eval 已具备基础能力，但还没有可视化 dashboard。
8. 后续计划
接入真实 MCP server；
加入 hybrid retrieval：BM25 + embedding；
加入 reranker；
构建 Agent executor，将 Router、Memory、Skills、RAG、Tools 串成完整执行链；
增加人工确认机制；
增加 trace dashboard；
扩展更多失败样例和 eval 指标。

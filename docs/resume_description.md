# 简历项目描述：SupportOps Agent

## 项目名称

SupportOps Agent：面向企业支持场景的 RAG + MCP + Skills Agent 工程系统

## 项目简介

基于 Python 构建面向企业客服与技术支持、故障工单和日志排查场景的 Agent 工程项目，围绕 Hybrid RAG、Neo4j 风格 GraphRAG、Intent Router、Case State Memory、MCP Mock Tools、Skills SOP、Agentic Retrieval Planner、Trace 和 Eval 进行模块化设计。项目重点不是简单调用大模型 API，而是模拟企业 Agent 在真实约束下会遇到的工程问题，包括工具召回不全、路由高置信错误、多轮记忆丢失、工具写操作安全、图谱关系检索和失败不可观测等。

## 技术栈

Python、pytest、uv、BM25、Hybrid RAG、SimpleVectorStore、Neo4j GraphRAG schema、Agent Router、Case State Memory、MCP Mock Tools、Skills、Trace、Eval、Git、Dify/Coze Workflow Design

## 核心工作

1. 实现 RAG MVP，从 Markdown 知识库加载文档、chunking、BM25 检索并返回 citation；
2. 针对中文无空格查询召回失败问题，改造 tokenizer，并补充 regression test；
3. 实现 Intent Router，支持登录、退款、API Key、RAG 上传失败、权限、部署错误等多类意图；
4. 构建 gold cases 和 router tests，定位并约束高置信错误路由风险；
5. 实现结构化 case_state memory，维护 user_id、plan、error_code、uploaded_file_type、attempted_steps 等多轮状态；
6. 实现 MCP Mock Tools，模拟用户、账单、工单和日志系统；
7. 对退款申请和工单创建等写操作默认采用 dry-run，避免模型直接执行有副作用动作；
8. 设计 Skills SOP 层，将退款、登录排查、API Key 恢复、RAG 上传失败排查等流程显式化；
9. 实现 TraceRecorder，记录 router_result、selected_skill、case_state、citations、tool_calls、final_answer 和 warnings；
10. 实现 router confusion、memory regression、RAG grounding 等 eval 脚本，并生成评估报告。
11. 实现 SimpleVectorStore 和 HybridRetriever，用 BM25 + Vector 融合提高语义召回并保持 citation；
12. 设计 Neo4j 风格 GraphRAG schema 和 in-memory graph fallback，支持 user/project/upload/error/service/ticket 关系检索；
13. 实现 Agentic Retrieval Planner 和 evidence sufficiency check，在证据不足时进行 query rewrite、graph expand 和 tool retry；
14. 编写 Dify/Coze workflow 对照文档，说明低代码原型与 Python 工程版在测试、Trace/Eval、工具安全和 GraphRAG 定制上的差异。

## 真实挑战与解决方案

### 1. 中文 RAG 召回失败

问题：单元测试通过，但真实输入“上传PDF后检索不到内容怎么办？”无法召回对应文档。

解决：将 tokenizer 改为中英文混合策略，英文/数字按词切分，中文按字符切分，并补充无空格中文查询回归测试。

### 2. 高置信错误路由

问题：“上传 PDF 后检索不到内容”可能被错误路由到 permission_issue。

解决：Router 输出 intent、confidence、reason、matched_keywords，并使用 gold cases 和回归测试约束高风险样例。

### 3. 多轮记忆丢失

问题：长对话中用户第一轮提供的 user_id、plan、error_code 后续容易丢失。

解决：设计结构化 case_state，每轮更新关键信息，并用 memory regression tests 验证状态不会丢失。

### 4. 工具写操作安全

问题：Agent 不能直接执行退款、创建工单这类有副作用的动作。

解决：MCP Mock Tools 中写操作默认 dry_run=True，只返回 action proposal，后续必须经过确认才能执行。

### 5. 企业 SOP 不明确

问题：Router 只能判断意图，不能保证 Agent 按企业业务流程处理。

解决：引入 Skills 层，把退款、登录排查、API Key 恢复、RAG 上传失败排查等流程写成 SKILL.md，明确必须收集的信息、可用工具、禁止事项和升级人工条件。

### 6. Agent 失败不可观测

问题：Agent 回答错时，很难判断是 RAG、Router、Memory、Tool 还是 Skill 出问题。

解决：实现 TraceRecorder 和多类 eval，将失败模式转化为可复盘、可测试、可回归的工程指标。

### 7. 单次 RAG 无法完成复杂故障排查

问题：上传失败、embedding 错误和历史工单之间存在 user、project、service、ticket 多跳关系，单纯文档检索无法定位根因链路。

解决：增加 Hybrid RAG、GraphRAG 和 Agentic Retrieval Planner。Hybrid RAG 提升语义召回，GraphRAG 提供实体关系证据，Planner 根据证据缺口决定是否重写查询、扩展图谱或调用 mock tools。

## 简历精简版

IncidentOps GraphRAG Agent：面向企业故障工单、日志和知识库的根因分析 Agent。基于 Python 构建 Hybrid RAG、Neo4j 风格 GraphRAG、意图路由、结构化多轮记忆、MCP Mock Tools、Skills SOP、Agentic Retrieval Planner、Trace 和 Eval 模块。实现中文 RAG 召回修复、高置信错误路由检测、case_state 长对话记忆、dry-run 工具写操作安全、图谱关系证据检索和 Agent 可观测评估体系，并补充 Dify/Coze workflow 对照文档。

## 面试讲法

这个项目不是普通客服机器人，而是我为了模拟企业级 Agent 工程问题设计的 IncidentOps 系统。它包含 Hybrid RAG、GraphRAG、Router、Memory、MCP Mock Tools、Skills、Agentic Retrieval Planner、Trace 和 Eval。Hybrid RAG 负责查政策和错误手册，GraphRAG 负责 user/project/error/service/ticket 关系链，Router 负责判断意图，Memory 负责维护多轮 case_state，MCP Mock Tools 模拟用户、账单、日志和工单系统，Skills 负责沉淀企业 SOP，Trace 和 Eval 用于复盘和评估。

项目中我刻意记录了多个真实问题，比如中文查询“上传PDF后检索不到内容”一开始无法召回正确文档，后来通过改造 tokenizer 和增加 regression test 解决；Router 可能高置信错误路由，所以我让它输出 confidence、reason 和 matched_keywords，并用 gold cases 约束；长对话中用户的 user_id、plan 和 error_code 容易丢失，所以我设计了结构化 case_state；写操作工具默认 dry-run，避免 Agent 直接执行退款或创建工单。

这个项目让我真正理解了 Agent 工程不是 prompt 写好就结束，而是要处理检索、路由、记忆、工具安全、业务流程和可观测性。

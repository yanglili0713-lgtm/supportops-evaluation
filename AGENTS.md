# AGENTS.md

你正在开发一个名为 SupportOps Agent 的企业级 Agent 项目。

## 项目目标

本项目不是普通聊天机器人，而是一个面向企业客服/技术支持场景的 Agent 系统。项目重点是体现真实 Agent 工程问题，包括：

1. RAG 检索不稳定；
2. 工具调用没有正确召回；
3. 多轮对话中 case 信息丢失；
4. 路由器高置信度但选错 skill；
5. MCP 工具权限和写操作安全；
6. Agent 执行过程 trace 和 eval。

## 技术栈

- Python 3.12
- FastAPI
- SQLite
- BM25 + Embedding 混合检索
- DeepSeek API 或 OpenAI 兼容 API
- MCP Python SDK
- pytest

## 开发原则

1. 每次只实现一个小模块，不要一次性生成整个项目。
2. 所有外部 API Key 必须放在 `.env`，不得写入源码。
3. 所有工具调用必须记录 trace。
4. 所有写操作必须先 dry-run，再确认执行。
5. 每个核心模块必须配最小测试。
6. 代码优先清晰、可解释，不追求复杂架构。
7. 每次修改后运行相关测试。
8. 不要删除已有文档，除非明确要求。
9. 如果需求不明确，先在 TODO 中标注，不要自行扩大范围。

## 项目模块

- app/router.py：意图路由器
- app/memory.py：结构化 case_state 记忆
- app/agent_loop.py：Agent 主流程
- app/verifier.py：证据校验器
- rag/retriever.py：RAG 检索
- rag/eval.py：RAG 评估
- mcp_servers/：模拟企业外部系统
- skills/：业务 SOP
- evals/：路由、工具召回、记忆回归、RAG grounding 测试
- traces/：每次运行的 trace 输出

## 项目阶段

第一阶段只做 CLI MVP：

用户输入问题
→ Router 判断意图
→ RAG 检索知识库
→ 输出带引用的回答
→ 保存 trace

不要在第一阶段做复杂前端。

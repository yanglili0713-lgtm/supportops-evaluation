# SupportOps Agent

SupportOps Agent 是一个面向企业客服与技术支持场景的 Agent 工程项目。

项目目标不是做普通聊天机器人，而是构建一个有真实约束的企业支持 Agent，用于实践：

- RAG 知识库检索
- MCP 外部工具调用
- Skills 业务 SOP
- 多轮 case_state 记忆
- 意图路由
- 工具召回评估
- RAG grounding 评估
- trace 观测

## 当前阶段

当前只做 Phase 0 和 Phase 1：

用户输入问题
→ Router 判断意图
→ RAG 检索知识库
→ 输出带 citation 的回答
→ 保存 trace

## 不提交的文件

`.env`、真实 API Key、本地数据库和运行 trace 不允许提交。

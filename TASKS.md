# TASKS.md

## Phase 0：项目初始化

- [ ] 创建 Python 项目结构
- [ ] 配置 pyproject.toml
- [ ] 创建 .env.example
- [ ] 创建基础 README
- [ ] 创建 pytest 配置

## Phase 1：RAG MVP

- [ ] 创建 data/docs 下的模拟知识库文档
- [ ] 实现 rag/ingest.py
- [ ] 实现 rag/chunker.py
- [ ] 实现 rag/retriever.py
- [ ] 支持 BM25 检索
- [ ] 返回 citation
- [ ] 添加 tests/test_retriever.py

## Phase 2：Router

- [ ] 实现 app/router.py
- [ ] 支持 login_issue、billing_refund、api_key_issue、rag_upload_issue、permission_issue、deployment_error、general_faq、unknown
- [ ] 输出 intent、confidence、reason
- [ ] 添加 gold_cases.jsonl
- [ ] 添加 evals/test_router.py

## Phase 3：Memory

- [ ] 实现 app/memory.py
- [ ] 定义 case_state
- [ ] 从多轮对话中抽取 user_id、plan、error_code、attempted_steps、missing_info
- [ ] 添加 memory regression tests

## Phase 4：MCP Mock Servers

- [ ] 实现 mcp_servers/user_server.py
- [ ] 实现 mcp_servers/billing_server.py
- [ ] 实现 mcp_servers/ticket_server.py
- [ ] 实现 mcp_servers/logs_server.py
- [ ] 所有写操作先 dry-run

## Phase 5：Skills

- [ ] 创建 skills/refund_policy/SKILL.md
- [ ] 创建 skills/login_troubleshooting/SKILL.md
- [ ] 创建 skills/api_key_recovery/SKILL.md
- [ ] 创建 skills/rag_upload_debug/SKILL.md
- [ ] 创建 skills/escalation/SKILL.md

## Phase 6：Trace and Eval

- [ ] 每次运行保存 traces/runs/*.json
- [ ] 实现 tool_recall_eval
- [ ] 实现 router_confusion_eval
- [ ] 实现 memory_regression_eval
- [ ] 实现 rag_grounding_eval
- [ ] 生成 evals/report.md

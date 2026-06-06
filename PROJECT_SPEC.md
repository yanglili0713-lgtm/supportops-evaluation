# PROJECT_SPEC.md

# SupportOps Agent 项目说明

## 1. 项目背景

企业客服和技术支持场景中，用户问题往往需要结合知识库、用户信息、账单信息、日志信息和工单系统进行处理。

普通 RAG 问答只能检索文档，无法完成完整业务流程；普通工具调用 Agent 又容易出现工具召回错误、长对话状态丢失、路由错误和越权操作等问题。

本项目希望构建一个小型但真实约束明确的企业支持 Agent，用于展示 RAG、MCP、Skills、Memory、Router、Eval 和 Trace 的工程整合能力。

## 2. 核心目标

构建一个 SupportOps Agent，可以处理以下类型问题：

1. 登录失败；
2. API Key 失效；
3. 上传 PDF 后 RAG 检索不到内容；
4. 账单和退款问题；
5. 团队权限不足；
6. 部署或接口报错；
7. 需要升级人工工单。

## 3. 系统流程

用户问题
→ Intent Router
→ Skill Selector
→ RAG 检索知识库
→ MCP 工具查询外部系统
→ Answer Verifier 检查证据
→ 输出回答或升级人工
→ 保存 trace

## 4. RAG 负责什么

RAG 用于检索：

- 产品 FAQ
- 退款政策
- API Key 指南
- RAG 上传失败排查文档
- 权限说明
- 错误码手册
- 部署指南

RAG 必须返回 citation，包括文档名和 chunk_id。

## 5. MCP 负责什么

MCP server 用于模拟企业外部系统：

- user_server：查询用户资料、套餐、权限；
- billing_server：查询账单、退款状态；
- ticket_server：创建和查询工单；
- logs_server：查询错误日志。

## 6. Skills 负责什么

Skills 是业务 SOP，例如：

- refund_policy
- login_troubleshooting
- api_key_recovery
- rag_upload_debug
- escalation

每个 Skill 必须说明：

- 适用场景；
- 必须收集的信息；
- 允许调用的工具；
- 禁止事项；
- 何时升级人工。

## 7. 重点工程挑战

项目必须刻意暴露并解决以下问题：

1. 工具调用没被正确召回；
2. 多轮对话中 user_id、plan、error_code 丢失；
3. router 高置信度但选错 intent；
4. RAG 检索到文档但回答缺少证据；
5. 写操作工具需要权限控制和 dry-run。

## 8. 第一阶段验收标准

第一阶段 MVP 验收：

- 能从 CLI 输入问题；
- 能输出 intent；
- 能检索知识库；
- 能返回 citation；
- 能保存 trace；
- 至少有 10 条 gold cases；
- pytest 能跑通。

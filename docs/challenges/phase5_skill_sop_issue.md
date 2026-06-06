# Phase 5 真实挑战记录：用 Skills 显式化企业 SOP，避免 Agent 自由发挥

## 1. 问题背景

在 Phase 2 中，我实现了 Intent Router，可以将用户问题路由到不同 intent，例如：

- billing_refund
- login_issue
- api_key_issue
- rag_upload_issue
- permission_issue
- deployment_error
- unknown

但是 Router 只能回答“这个问题属于哪类”，不能保证 Agent 后续一定按照企业业务流程处理。

例如：

```text
用户：我想退款。
Router 可以判断为：

billing_refund

但这并不等于 Agent 知道应该：

先确认 user_id；
查询 invoice；
判断是否在退款窗口内；
判断 usage_ratio 是否超过限制；
默认 dry-run 创建退款申请；
不能直接承诺退款成功；
不满足条件时升级人工。

因此，企业 Agent 不能只依赖 Router，还需要把业务 SOP 显式沉淀成 Skills。

2. 真实风险

如果没有 Skills，Agent 可能出现以下问题：

只根据意图直接回答，忽略必要信息收集；
未查询 invoice 就承诺退款；
未查询日志就判断 RAG 上传失败原因；
忽略 dry-run，直接执行有副作用的工具；
在证据不足时没有升级人工；
不同问题的处理步骤不一致，无法稳定复现。

这类问题在 demo 中不明显，但在企业客服、技术支持、工单处理场景中非常关键。

3. 解决方案

Phase 5 中，我新增了 Skills 层，将业务流程显式化。

新增 Skill 包括：

refund_policy
login_troubleshooting
api_key_recovery
rag_upload_debug
escalation

每个 SKILL.md 都包含固定结构：

适用场景
必须收集的信息
可用 RAG 文档
可用 MCP Mock Tools
禁止事项
处理步骤
升级人工条件
输出模板

这样 Agent 不再是“自由发挥”，而是根据 intent 选择对应 Skill，再按照 Skill 中定义的 SOP 进行处理。

4. Skill Selector 设计

Phase 5 中新增了：

app/skill_loader.py
app/skill_selector.py

其中：

skill_loader.py 负责加载 skills/*/SKILL.md；
skill_selector.py 负责根据 Router intent 选择 Skill。

当前映射关系：

billing_refund  → refund_policy
login_issue     → login_troubleshooting
api_key_issue   → api_key_recovery
rag_upload_issue→ rag_upload_debug
unknown         → escalation

对于暂未精细实现的 intent，例如 permission_issue 和 deployment_error，可以先走 escalation 或保留 TODO，避免 Agent 在流程不明确时乱处理。

5. 和 RAG / MCP / Memory 的关系

Skills 层不是孤立模块，而是连接前面几个阶段：

Router：决定当前问题属于哪个 intent；
Memory：提供 user_id、plan、error_code、invoice_id 等 case_state；
RAG：提供政策、FAQ、错误手册等依据；
MCP Mock Tools：查询用户、账单、日志、工单系统；
Skills：规定什么时候查什么、不能做什么、何时升级人工。

例如 refund_policy Skill 会要求：

必须收集 user_id；
必须查询 invoice；
必须检查退款窗口；
写操作必须 dry-run；
不能直接承诺退款成功；
条件不满足时升级人工。

这体现了企业 Agent 中 “intent → SOP → tool execution” 的流程约束。

6. 回归测试

Phase 5 新增 tests/test_skills.py，测试覆盖：

能加载所有 SKILL.md；
每个 SKILL.md 都包含固定章节；
billing_refund 能选择 refund_policy；
rag_upload_issue 能选择 rag_upload_debug；
api_key_issue 能选择 api_key_recovery；
login_issue 能选择 login_troubleshooting；
unknown 能选择 escalation；
不存在的 skill_name 返回 None 或结构化错误。

测试结果：

39 passed
7. 项目经验总结

这个阶段让我意识到，企业 Agent 不是“模型会判断意图”就够了。

Router 解决的是分类问题，Skills 解决的是流程约束问题。

如果没有 Skills，Agent 很容易根据模型直觉自由发挥；而通过 Skill SOP，可以把企业规则、工具权限、必要信息、禁止事项和升级条件显式写下来，使 Agent 行为更稳定、更可审计。

8. 面试表述

在 Phase 5 中，我重点解决的是 Router 和业务流程之间的断层问题。Router 可以判断用户问题是退款、API Key、登录还是 RAG 上传失败，但它不能保证 Agent 按企业 SOP 做事。

比如退款问题，Agent 不能直接承诺退款成功，必须先确认 user_id，查询 invoice，判断退款窗口和 usage_ratio，并且 create_refund_request 必须默认 dry-run。为了解决这个问题，我增加了 Skills 层，把 refund_policy、login_troubleshooting、api_key_recovery、rag_upload_debug 等业务流程写成 SKILL.md，每个 Skill 明确适用场景、必须收集的信息、可用工具、禁止事项、处理步骤和升级人工条件。

这样项目从“能路由问题”进一步变成了“能按企业流程处理问题”。

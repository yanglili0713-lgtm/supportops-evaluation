# Phase 4 真实挑战记录：MCP 工具写操作安全与 dry-run 机制

## 1. 问题背景

在企业支持 Agent 中，Agent 不仅需要回答问题，还需要查询外部系统，例如用户系统、账单系统、日志系统和工单系统。

Phase 4 中，我将这些外部系统抽象成 mock MCP tools：

- user_server：查询用户资料、套餐和权限；
- billing_server：查询账单、退款状态和创建退款申请；
- ticket_server：创建和查询工单；
- logs_server：查询错误日志。

当前阶段没有接入真实 MCP 网络协议，而是先用本地 mock server / mock tool 函数模拟企业工具调用流程。

---

## 2. 真实风险

Agent 调用工具的风险不在于“能不能调通”，而在于：

```text
模型可能在证据不足、权限不足或用户未确认的情况下执行写操作。
例如：

用户：我想退款。

如果 Agent 直接调用：

create_refund_request(user_id, reason)

就可能产生错误退款申请。

再比如：

用户：帮我建个工单。

如果 Agent 直接创建工单，可能造成重复工单、错误分类或无效工单。

因此，企业 Agent 的工具调用必须区分：

read-only 查询；
write-draft 写入草案；
write-confirmed 用户确认后的写操作。
3. 解决方案

Phase 4 中，我将写操作默认设计为：

dry_run=True

包括：

create_refund_request(user_id, reason, dry_run=True)
create_ticket(user_id, issue_type, summary, dry_run=True)

默认情况下，这些工具不会真正写入或执行，而是返回一个 action proposal。

返回结构包含：

ok
action
data
error
dry_run

这样 Agent 可以先把准备执行的动作展示给用户或上层 verifier，再决定是否继续执行。

4. 工程意义

dry-run 机制可以避免以下问题：

模型误判业务意图后直接执行写操作；
用户没有明确确认时产生副作用；
重复创建退款申请或工单；
工具调用结果无法审计；
后续无法区分“计划执行”和“已经执行”。

在企业环境中，Agent 工具调用必须具备权限控制、参数校验、审计日志和可回滚设计。Phase 4 先用 dry-run 机制实现最小安全边界。

5. 回归测试

Phase 4 新增 tests/test_mcp_servers.py，测试覆盖：

能根据 user_id 查到用户资料；
能查到用户套餐；
能查到用户权限；
能根据 invoice_id 或 user_id 查到账单；
refund 写操作默认 dry_run=True；
ticket 写操作默认 dry_run=True；
能按 error_code 查询日志；
查询不存在用户时返回 ok=False 和 error。

测试结果：

29 passed
6. 项目经验总结

这个阶段让我意识到，Agent 工具调用不是“把函数暴露给模型”就结束了。

真正的企业级约束包括：

哪些工具是只读；
哪些工具有副作用；
写操作是否需要 dry-run；
用户是否确认；
调用结果是否可追踪；
调用失败是否有结构化错误。

因此我在 Phase 4 中先把所有写操作默认做成 dry-run，确保 Agent 只生成 action proposal，而不是直接执行真实动作。

7. 面试表述

在 Phase 4 中，我重点处理的是 Agent 工具调用的写操作安全问题。很多 Agent demo 只是把函数暴露给模型，但企业场景里不能让模型直接执行退款、创建工单这类有副作用的操作。

我的做法是把外部系统先抽象成 mock MCP tools，包括用户、账单、工单和日志系统。对于 create_refund_request 和 create_ticket 这类写操作，默认 dry_run=True，只返回 action proposal，不直接执行。这样可以把“模型想做什么”和“系统真正执行什么”分开，后续再接入用户确认、权限控制和审计日志。

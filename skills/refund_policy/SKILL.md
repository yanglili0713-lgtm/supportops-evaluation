# refund_policy

## 适用场景

用户咨询退款、账单、发票、扣费异常、订单状态或退款进度。Router intent 通常是 `billing_refund`。

## 必须收集的信息

- `user_id`：来自 Memory 的 `case_state.user_id`，缺失时先询问。
- `invoice_id`：来自用户消息或 Memory 的 `case_state.invoice_id`；如果只有 `user_id`，可先查询该用户账单。
- 退款原因：例如误扣费、重复支付、服务不可用、购买后不符合预期。
- 套餐和使用情况：优先使用 `get_user_plan(user_id)` 和 `get_invoice(...)` 返回的信息。

## 可用 RAG 文档

- `data/docs/refund_policy.md`
- 产品 FAQ 中与账单、退款、发票相关的片段。

## 可用 MCP Mock Tools

- `mcp_servers.user_server.get_user_profile(user_id)`
- `mcp_servers.user_server.get_user_plan(user_id)`
- `mcp_servers.billing_server.get_invoice(invoice_id=None, user_id=None)`
- `mcp_servers.billing_server.get_refund_status(user_id)`
- `mcp_servers.billing_server.create_refund_request(user_id, reason, dry_run=True)`
- `mcp_servers.ticket_server.create_ticket(user_id, issue_type, summary, dry_run=True)`

## 禁止事项

- 不得承诺一定退款成功，只能说明根据政策和 mock 数据的初步判断。
- 不得读取或要求用户提供真实银行卡、完整支付凭证或真实 API Key。
- 不得在未 dry-run 和未获得用户确认前创建退款请求。
- 不得调用真实支付、账单或工单系统。

## 处理步骤

1. 从 Memory 读取 `user_id`、`invoice_id`、`plan` 和历史对话中的退款原因。
2. 缺少 `user_id` 时先询问用户；缺少 `invoice_id` 时用 `get_invoice(user_id=...)` 查询候选账单。
3. 用 RAG 检索 `refund_policy.md`，回答必须带 citation。
4. 用 `get_invoice(...)` 查看账单状态、金额、支付日期和使用比例。
5. 用 `get_refund_status(user_id)` 检查是否已有退款请求。
6. 如满足初步条件，调用 `create_refund_request(..., dry_run=True)` 返回 action proposal。
7. 明确要求用户确认后，才允许后续流程把 `dry_run` 改为 `False`；本阶段不得自动执行。
8. 如果政策或账单数据不足，创建人工工单也必须先 `create_ticket(..., dry_run=True)`。

## 升级人工条件

- 用户拒绝提供必要的 `user_id` 或无法确认账单。
- 账单状态、使用比例或退款政策存在冲突。
- 用户要求强制退款、投诉升级、企业合同退款或税务发票特殊处理。
- mock tool 返回 `ok=False` 且无法通过补充信息恢复。

## 输出模板

```text
问题类型：账单/退款
已确认信息：user_id={user_id}，invoice_id={invoice_id}，plan={plan}
知识库依据：{citations}
账单/退款状态：{tool_result_summary}
建议操作：{dry_run_proposal_or_next_question}
需要你确认：{confirmation_needed}
```

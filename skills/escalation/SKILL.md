# escalation

## 适用场景

Router intent 为 `unknown`，或当前阶段尚未有专用 Skill，例如 `permission_issue`、`deployment_error`，或多个工具/RAG 结果冲突需要人工判断。

## 必须收集的信息

- `user_id`：用于创建工单和关联日志。
- `intent` 或 `last_router_intent`：说明为什么进入升级流程。
- 问题摘要：用户原始描述、错误码、影响范围和已尝试步骤。
- 相关证据：RAG citation、mock tool 返回结果和 Memory 中的 case_state。

## 可用 RAG 文档

- `data/docs/permission_guide.md`
- `data/docs/error_code_manual.md`
- `data/docs/api_key_guide.md`
- `data/docs/rag_upload_troubleshooting.md`
- `data/docs/refund_policy.md`

## 可用 MCP Mock Tools

- `mcp_servers.user_server.get_user_profile(user_id)`
- `mcp_servers.logs_server.search_error_logs(user_id=None, error_code=None)`
- `mcp_servers.ticket_server.search_tickets(user_id)`
- `mcp_servers.ticket_server.create_ticket(user_id, issue_type, summary, dry_run=True)`

## 禁止事项

- 不得把不确定结论包装成确定答案。
- 不得调用真实工单系统。
- 不得在未 dry-run 和用户确认前创建工单。
- 不得要求用户提供真实 API Key、密码、token 或敏感文件。

## 处理步骤

1. 汇总 Memory 中的 `case_state`，包括 `user_id`、`intent`、`error_code`、`attempted_steps` 和 `missing_info`。
2. 若缺少 `user_id`，先询问；如果用户无法提供，说明只能给一般建议。
3. 对 `permission_issue`，TODO：后续应新增专用权限 Skill；当前先参考 `permission_guide.md` 并查询 `get_user_profile`。
4. 对 `deployment_error`，TODO：后续应新增部署排错 Skill；当前先参考错误码手册并查询日志。
5. 检查已有工单：`search_tickets(user_id)`。
6. 需要升级时，调用 `create_ticket(..., dry_run=True)` 生成工单 proposal。
7. 明确列出将提交的 issue_type、summary 和证据，等待用户确认。

## 升级人工条件

- Router intent 为 `unknown`。
- 权限或部署问题缺少当前阶段专用 Skill。
- RAG 证据不足、工具返回冲突或用户影响范围较大。
- 涉及安全、合规、企业合同或真实系统写操作。

## 输出模板

```text
问题类型：需要人工升级
升级原因：{reason}
已确认信息：{case_state_summary}
证据：{citations_and_tool_results}
工单草案：{dry_run_ticket}
需要你确认：是否按上述内容创建工单
```

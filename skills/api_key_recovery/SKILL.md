# api_key_recovery

## 适用场景

用户反馈 API Key 失效、鉴权失败、`API_KEY_INVALID`、`401`、`unauthorized`、密钥被删除或换过 API Key 仍失败。Router intent 通常是 `api_key_issue`。

## 必须收集的信息

- `user_id`：用于查询用户资料、套餐和权限。
- `plan`：来自 Memory 或 `get_user_plan(user_id)`。
- `error_code`：例如 `API_KEY_INVALID`。
- 已尝试步骤：例如 `换过 API Key`。
- 发生问题的接口类型和时间范围，便于查日志。

## 可用 RAG 文档

- `data/docs/api_key_guide.md`
- `data/docs/error_code_manual.md`
- 权限相关问题可参考 `data/docs/permission_guide.md`

## 可用 MCP Mock Tools

- `mcp_servers.user_server.get_user_profile(user_id)`
- `mcp_servers.user_server.get_user_plan(user_id)`
- `mcp_servers.user_server.get_user_permissions(user_id)`
- `mcp_servers.logs_server.search_error_logs(user_id=None, error_code=None)`
- `mcp_servers.ticket_server.create_ticket(user_id, issue_type, summary, dry_run=True)`

## 禁止事项

- 不得读取、生成、打印或要求用户粘贴真实 API Key。
- 不得尝试创建真实密钥或调用真实鉴权服务。
- 不得绕过套餐、权限或安全限制。
- 创建人工工单前必须 dry-run 并等待用户确认。

## 处理步骤

1. 从 Memory 读取 `user_id`、`plan`、`error_code`、`attempted_steps`。
2. 缺少 `user_id` 时先询问；不要要求真实 API Key。
3. 调用 `get_user_plan(user_id)` 和 `get_user_permissions(user_id)` 检查套餐与权限。
4. 用 RAG 检索 `api_key_guide.md` 和错误码手册，回答必须引用来源。
5. 如果有 `error_code`，调用 `search_error_logs(error_code=...)`；如果有 `user_id`，可按用户查询日志。
6. 如果用户已 `换过 API Key`，优先检查套餐、权限、环境变量或调用项目是否一致。
7. 无法定位时，调用 `create_ticket(..., dry_run=True)` 生成工单 proposal。

## 升级人工条件

- mock 日志显示异常但文档没有覆盖。
- 套餐和权限正常，但仍持续 `API_KEY_INVALID` 或 `401`。
- 涉及密钥泄露、误删、企业审计或安全事件。
- 用户要求恢复已删除密钥。

## 输出模板

```text
问题类型：API Key 故障
已确认信息：user_id={user_id}，plan={plan}，error_code={error_code}
权限/日志检查：{tool_result_summary}
知识库依据：{citations}
建议排查：{steps}
下一步：{next_action_or_dry_run_ticket}
```

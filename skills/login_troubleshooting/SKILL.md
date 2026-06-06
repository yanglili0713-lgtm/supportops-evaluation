# login_troubleshooting

## 适用场景

用户反馈登录失败、登录态过期、无法登录、验证码异常、密码相关问题或反复跳回登录页。Router intent 通常是 `login_issue`。

## 必须收集的信息

- `user_id`：用于查询用户资料和关联日志。
- 登录失败现象：登录态过期、验证码失败、密码失败、页面跳转循环。
- 已尝试步骤：例如 `重新登录过`、清理缓存、换浏览器。
- 错误码：如用户提到 `SESSION_EXPIRED` 或其他大写错误码，写入 Memory。

## 可用 RAG 文档

- 产品 FAQ 中登录和账号相关片段。
- `data/docs/error_code_manual.md`

## 可用 MCP Mock Tools

- `mcp_servers.user_server.get_user_profile(user_id)`
- `mcp_servers.logs_server.search_error_logs(user_id=None, error_code=None)`
- `mcp_servers.ticket_server.create_ticket(user_id, issue_type, summary, dry_run=True)`

## 禁止事项

- 不得要求用户提供密码、验证码原文、会话 token 或 cookie。
- 不得尝试重置真实账号或调用真实身份系统。
- 不得在未确认前创建工单；创建工单必须先 dry-run。

## 处理步骤

1. 从 Memory 读取 `user_id`、`attempted_steps`、`error_code`。
2. 缺少 `user_id` 时先询问，避免查错用户。
3. 用 RAG 检索错误码手册或登录 FAQ，输出排查步骤时带 citation。
4. 如果有 `user_id` 或 `error_code`，调用 `search_error_logs(...)` 查看 mock 日志。
5. 根据用户已尝试步骤避免重复建议，例如已 `重新登录过` 时不要只建议重新登录。
6. 如仍无法定位，调用 `create_ticket(..., dry_run=True)` 生成升级工单 proposal。

## 升级人工条件

- 多次尝试后仍登录失败。
- 日志显示账号状态异常但 mock 工具无法处理。
- 用户无法提供必要身份信息。
- 涉及企业 SSO、权限继承、账号冻结或安全事件。

## 输出模板

```text
问题类型：登录故障
已确认信息：user_id={user_id}，error_code={error_code}
已尝试步骤：{attempted_steps}
日志线索：{log_summary}
建议排查：{steps_with_citations}
下一步：{next_action_or_dry_run_ticket}
```

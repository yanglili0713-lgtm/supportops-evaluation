# rag_upload_debug

## 适用场景

用户反馈上传 PDF、docx 或 txt 后，知识库检索不到内容、召回不到、索引失败、embedding 失败或 RAG 返回无依据。Router intent 通常是 `rag_upload_issue`。

## 必须收集的信息

- `user_id`：用于查询日志和创建工单。
- `uploaded_file_type`：例如 `PDF`、`docx`、`txt`。
- `error_code`：例如 `EMBEDDING_FAILED`。
- 已尝试步骤：例如 `重新上传过`。
- 文件是否为扫描件、是否完成 OCR、是否超过大小限制。

## 可用 RAG 文档

- `data/docs/rag_upload_troubleshooting.md`
- `data/docs/error_code_manual.md`

## 可用 MCP Mock Tools

- `mcp_servers.logs_server.search_error_logs(user_id=None, error_code=None)`
- `mcp_servers.user_server.get_user_profile(user_id)`
- `mcp_servers.ticket_server.create_ticket(user_id, issue_type, summary, dry_run=True)`

## 禁止事项

- 不得要求用户上传包含敏感数据的真实文件到外部服务。
- 不得声称已经重新索引真实知识库；本阶段只能基于 mock 数据排查。
- 不得在用户未确认时创建工单；必须先 dry-run。

## 处理步骤

1. 从 Memory 读取 `user_id`、`uploaded_file_type`、`error_code`、`attempted_steps`。
2. 缺少 `uploaded_file_type` 时先询问文件类型；缺少 `user_id` 时询问用户标识。
3. 用 RAG 检索 `rag_upload_troubleshooting.md`，优先回答 PDF 扫描件、OCR、分块、索引和 embedding 问题。
4. 如果用户提到 `EMBEDDING_FAILED`，调用 `search_error_logs(error_code="EMBEDDING_FAILED")`。
5. 如果用户已 `重新上传过`，不要重复建议只重新上传，改为检查 OCR、索引状态和错误日志。
6. 若日志与文档都不能解释，调用 `create_ticket(..., dry_run=True)` 生成升级 proposal。

## 升级人工条件

- `EMBEDDING_FAILED` 持续出现。
- 文档格式受支持但仍无法检索。
- 用户已重新上传、重建索引后仍失败。
- 需要检查真实文件内容、索引任务或后台队列。

## 输出模板

```text
问题类型：RAG 上传/检索故障
已确认信息：user_id={user_id}，file_type={uploaded_file_type}，error_code={error_code}
已尝试步骤：{attempted_steps}
知识库依据：{citations}
日志线索：{log_summary}
建议排查：{steps}
下一步：{next_action_or_dry_run_ticket}
```

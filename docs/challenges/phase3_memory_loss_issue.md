# Phase 3 真实挑战记录：多轮对话中的关键信息丢失

## 1. 问题背景

在企业支持 Agent 中，用户往往不会一次性说完所有信息，而是在多轮对话中逐步补充：

- 第一轮提供 user_id；
- 第二轮说明自己是 pro 套餐；
- 第三轮描述上传 PDF 后检索不到内容；
- 第四轮才提供错误码 EMBEDDING_FAILED；
- 后续又问“那我现在该怎么办”。

如果 Agent 只依赖最近几轮原文，前面提供的 user_id、plan、error_code 等关键信息很容易在长对话中丢失。

---

## 2. 真实风险

长对话中最常见的问题不是模型完全不能回答，而是：

```text
用户前面已经说过的信息，Agent 后面又重复追问。
例如：

第一轮：我的 user_id 是 u_1001。
第二轮：我是 pro 套餐。
第三轮：我上传 PDF 后检索不到内容。
第四轮：报错是 EMBEDDING_FAILED。
第五轮：那我现在该怎么办？

如果没有结构化记忆，第五轮 Agent 可能忘记：

用户 ID 是 u_1001；
用户是 pro 套餐；
文件类型是 PDF；
错误码是 EMBEDDING_FAILED；
当前问题属于 RAG 上传 / embedding 失败排查。

这会导致 Agent 重复追问、错误路由，甚至调用错误工具。

3. 解决方案

Phase 3 中，我没有简单扩大上下文窗口，而是实现了结构化 case_state 记忆。

case_state 至少记录：

user_id
plan
intent
error_code
invoice_id
uploaded_file_type
attempted_steps
missing_info
last_router_intent
current_decision

每一轮对话结束后，通过 update_case_state 从用户消息和 Router 结果中抽取关键信息，并持续更新同一个 case_state。

这样后续对话不需要依赖完整历史，只需要注入结构化状态即可。

4. 工程实现

当前阶段采用规则、正则和简单字符串匹配，不调用真实 LLM。

可以抽取的信息包括：

u_1001 这类 user_id；
free、pro、enterprise 这类套餐；
EMBEDDING_FAILED、API_KEY_INVALID、PERMISSION_DENIED 这类错误码；
inv_9001 这类 invoice_id；
PDF、docx、txt 等文件类型；
“重新上传过”“重新登录过”“换过 API Key”等已尝试步骤。

如果缺少关键信息，例如 user_id，则写入 missing_info。

5. 回归测试

Phase 3 新增 tests/test_memory.py，用于验证多轮信息不会丢失。

测试覆盖：

第一轮给出 user_id，第三轮仍然保留；
第一轮说自己是 pro 套餐，后续仍然保留 plan；
用户说上传 PDF 后检索不到内容，case_state 记录 uploaded_file_type=PDF；
用户提到 EMBEDDING_FAILED，case_state 记录 error_code；
用户没有提供 user_id 时，missing_info 包含 user_id。

测试结果：

20 passed
6. 项目经验总结

这个问题让我意识到，长对话 Agent 不能只依赖原始聊天历史，也不能简单通过增大上下文窗口解决问题。

更工程化的做法是：

把自然语言历史压缩成结构化 case_state；
每轮更新 case_state；
每轮推理时注入 case_state；
用 memory regression tests 验证多轮后关键信息仍然存在。

这样可以把“模型记不记得”变成“状态字段是否被正确维护”的工程问题。

7. 面试表述

在 Phase 3 中，我重点解决的是长对话中的关键信息丢失问题。企业支持场景里，用户经常在多轮对话中逐步提供 user_id、套餐、错误码、文件类型和已尝试步骤。如果只依赖最近几轮上下文，Agent 很容易在后续重复追问或错误路由。

我的解决方式不是简单扩大上下文，而是设计结构化 case_state，把 user_id、plan、intent、error_code、uploaded_file_type、attempted_steps、missing_info 等字段持续维护起来。每轮对话结束后用 update_case_state 更新状态，再通过 memory regression tests 验证第三轮、第五轮仍然能保留第一轮提供的信息。这样把长对话记忆问题变成了可测试、可回归的状态管理问题。

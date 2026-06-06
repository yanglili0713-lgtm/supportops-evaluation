# Phase 2 真实挑战记录：高置信错误路由风险

## 1. 问题背景

在企业支持 Agent 中，用户问题需要先经过 Router 判断意图，再决定后续是否进入 RAG、调用工具、选择 Skill 或升级人工。

Phase 2 中，我实现了一个基于规则、关键词和简单打分的 Intent Router，支持以下 intent：

- login_issue
- billing_refund
- api_key_issue
- rag_upload_issue
- permission_issue
- deployment_error
- general_faq
- unknown

Router 输出包含：

- intent
- confidence
- reason
- matched_keywords

## 2. 真实风险

Router 最大的问题不是“完全不知道”，而是：

```text
置信度看起来很高，但实际路由错了。
例如用户输入：

上传 PDF 后检索不到内容

这个问题正确应该进入：

rag_upload_issue

因为它和文档解析、chunking、embedding、向量库写入、检索召回有关。

但如果规则设计不好，Router 可能因为“访问不到”“检索不到”“权限”等词误判成：

permission_issue

这会导致后续 Agent 选择错误 Skill，甚至调用错误工具。

3. 定位方式

我在 Phase 2 中要求 Router 保留以下 trace 字段：

predicted intent
confidence
matched keywords
reason

这样当路由错误时，可以反查：

是哪些关键词触发了错误 intent；
正确 intent 的关键词是否没有覆盖；
多个 intent 分数接近时是否需要降级为澄清问题；
是否存在“高置信但证据不足”的情况。
4. 解决方案

当前阶段采用规则 + 关键词 + 简单打分实现 Router，并通过 gold cases 约束高风险样例。

特别加入测试：

上传 PDF 后检索不到内容

必须路由到：

rag_upload_issue

并且不能误路由到：

permission_issue

这使得高置信错误路由风险可以被测试捕获，而不是只靠人工观察。

5. 回归测试

Phase 2 新增 data/gold_cases.jsonl 和 tests/test_router.py。

测试覆盖：

API Key 失效 → api_key_issue
上传 PDF 后检索不到内容 → rag_upload_issue
退款/发票/账单 → billing_refund
权限不足 → permission_issue
登录态过期 → login_issue
无法判断 → unknown
上传 PDF 检索失败不能误判为 permission_issue

测试结果：

13 passed
6. 项目经验总结

这个问题让我意识到，Agent Router 不能只输出一个 intent，还必须输出可解释信息，例如 confidence、reason 和 matched_keywords。

如果没有这些 trace，当模型或规则出现高置信错误路由时，很难判断到底是 prompt 问题、关键词问题、工具描述问题，还是业务 SOP 设计问题。

后续可以继续增强：

构造 router confusion matrix；
记录 high_confidence_wrong_route；
当多个 intent 分数接近时触发澄清问题；
用 RAG 证据或 Skill required evidence 反向校验 Router 结果。
7. 面试表述

在 Router 阶段，我遇到的核心问题是高置信错误路由风险。比如“上传 PDF 后检索不到内容”这个问题，如果 Router 只看“访问不到”“检索不到”等表面词，可能会错误路由到 permission_issue，但实际应该是 rag_upload_issue。

我没有只让 Router 返回 intent，而是让它同时返回 confidence、reason 和 matched_keywords，方便定位错误路由的触发原因。同时我构造了 gold cases 和回归测试，明确要求该样例不能误判为 permission_issue。这样路由问题就从“模型感觉对不对”变成了可测试、可回归、可解释的工程问题。

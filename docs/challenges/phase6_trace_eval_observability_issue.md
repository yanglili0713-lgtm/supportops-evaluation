# Phase 6 真实挑战记录：Agent 失败不可观测与 Trace/Eval 体系

## 1. 问题背景

在前几个阶段中，项目已经具备了 RAG、Router、Memory、MCP Mock Tools 和 Skills：

- RAG 负责知识库检索；
- Router 负责意图识别；
- Memory 负责维护结构化 case_state；
- MCP Mock Tools 负责模拟外部系统；
- Skills 负责企业 SOP 流程约束。

但是这些模块能跑通，并不代表系统可用于真实场景。真正的问题是：

```text
当 Agent 回答错误时，如何判断到底是哪一层出了问题？
可能的失败来源包括：

RAG 没有召回正确文档；
Router 高置信度但路由错误；
Memory 丢失了前几轮用户提供的信息；
Tool 没有被正确调用；
Skill 选择错误；
最终回答缺少 citation 或证据不足。

如果没有 trace 和 eval，这些问题很难定位。

2. 真实风险

没有可观测性的 Agent 只会给出一个最终答案，但无法回答这些问题：

用户原始问题是什么？
Router 选择了哪个 intent？
Router confidence 是否过高？
选择了哪个 Skill？
case_state 中是否保留了 user_id、plan、error_code？
RAG 返回了哪些 citation？
调用了哪些工具？
有没有 warning？
最终答案是否基于证据？

这会导致 Agent 项目停留在 demo 层面，无法复盘、无法评估、无法调试。

3. 解决方案

Phase 6 中，我新增了 Trace 和 Eval 体系。

新增：

app/tracing.py
evals/tool_recall_eval.py
evals/router_confusion_eval.py
evals/memory_regression_eval.py
evals/rag_grounding_eval.py
evals/run_all.py
tests/test_tracing_and_evals.py

其中 TraceRecorder 记录一次 Agent 运行过程，包括：

run_id
timestamp
user_message
router_result
selected_skill
case_state
retrieved_citations
tool_calls
final_answer
warnings

trace 默认保存到：

traces/runs/*.json

这样每次 Agent 执行都可以被复盘。

4. Eval 覆盖的失败模式

Phase 6 中新增了多个 eval：

4.1 tool_recall_eval

用于检查 gold cases 中的 expected_intent 是否能被 router 命中。

当前结果：

accuracy = 1.0
failed_cases = []
4.2 router_confusion_eval

用于生成 confusion matrix，并识别：

high_confidence_wrong_route

当前结果：

high_confidence_wrong_route = []

这说明当前 gold cases 下没有出现高置信错误路由。

4.3 memory_regression_eval

用于验证多轮对话中 case_state 是否丢失关键信息。

检查项包括：

user_id_persisted
plan_persisted
error_code_persisted
uploaded_file_type_persisted
attempted_steps_accumulated

当前结果：

passed = true
4.4 rag_grounding_eval

用于验证 RAG 是否返回 citation，以及是否召回指定文档。

测试问题包括：

上传 PDF 后检索不到内容；
用户想申请退款；
API Key 失效。

当前结果：

passed = true
5. 运行结果

Phase 6 测试结果：

44 passed in 0.05s

Eval 汇总结果：

Router accuracy: 1.0
High confidence wrong routes: []
Memory regression: passed
RAG grounding: passed
6. 项目经验总结

这一阶段让我意识到，企业级 Agent 不能只追求“能回答”，更重要的是“可复盘、可评估、可定位”。

如果一个 Agent 回答错了，不能只说“模型幻觉了”，而要能定位到底是：

Router 选错 intent；
RAG 没有召回正确文档；
Memory 丢失 case_state；
Tool 调用缺失；
Skill SOP 没有约束好；
Answer 没有 citation。

因此我增加了 TraceRecorder 和多类 eval，把 Agent 的失败模式拆解成可测试的工程指标。

7. 面试表述

在 Phase 6 中，我重点解决的是 Agent 失败不可观测的问题。前面虽然已经实现了 RAG、Router、Memory、MCP Mock Tools 和 Skills，但如果 Agent 回答错了，很难知道问题出在哪一层。

我的做法是增加 TraceRecorder，把一次运行中的 user_message、router_result、selected_skill、case_state、retrieved_citations、tool_calls、final_answer 和 warnings 全部保存下来。同时实现 router confusion eval、memory regression eval、RAG grounding eval 等评估脚本，能够检查高置信错误路由、长对话状态丢失和 RAG 证据不足等问题。

这样项目就不是一个只会输出答案的 demo，而是具备可观测、可评估、可复盘能力的 Agent 工程系统。

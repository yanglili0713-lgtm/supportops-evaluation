# Failure Analysis

## Overview

- Benchmark cases: 80
- Pipelines: dummy, naive, hybrid, graph, planner
- Trace rows: 400

| Pipeline | Cases | Recall@5 | Precision@5 | Refusal Acc | Route Acc | Avg Latency ms |
|---|---:|---:|---:|---:|---:|---:|
| dummy | 80 | 0.9563 | 0.7847 | 0.8375 | 0.7875 | 0.0097 |
| naive | 80 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.0852 |
| hybrid | 80 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.2589 |
| graph | 80 | 0.8646 | 0.8542 | 0.8500 | N/A | 0.0920 |
| planner | 80 | 0.9625 | 0.4421 | 0.8500 | 0.6250 | 1.4303 |

## Dummy: rule-aligned sanity baseline

Dummy Recall@5 is 0.9563 and Precision@5 is 0.7847.
This pipeline is a rule-based sanity baseline, not a weak baseline and not an oracle baseline.
It does not read expected_docs, gold labels, or benchmark answers. Its high score comes from hand-written rules and document taxonomy that are intentionally aligned with the local SupportOps seed benchmark.
Use dummy only to verify that the evaluation harness, schema adapter, metrics, trace writing, and report generation are working.

## Naive/Hybrid: high recall but low precision cases

Found 134 cases where naive/hybrid retrieved all expected evidence but mixed in noisy top-k documents.
Counts by pipeline: hybrid=67, naive=67.
Naive/hybrid retrieved_doc_ids overlap: same doc set in 80/80 cases; same ordered list in 43/80 cases.
When naive and hybrid have identical doc-level metrics, it usually means the current 5-doc seed corpus and doc-source-level @5 evaluation are too coarse to expose chunk/ranking/score differences.

- pipeline=naive; case_id=Q001; gold_intent=permission_issue; retrieved_doc_ids=['data/docs/permission_guide.md', 'data/docs/api_key_guide.md', 'data/docs/refund_policy.md', 'data/docs/error_code_manual.md']
- pipeline=naive; case_id=Q002; gold_intent=billing_refund; retrieved_doc_ids=['data/docs/refund_policy.md', 'data/docs/permission_guide.md', 'data/docs/rag_upload_troubleshooting.md', 'data/docs/api_key_guide.md', 'data/docs/error_code_manual.md']
- pipeline=naive; case_id=Q003; gold_intent=rag_upload_issue; retrieved_doc_ids=['data/docs/rag_upload_troubleshooting.md', 'data/docs/error_code_manual.md', 'data/docs/api_key_guide.md', 'data/docs/refund_policy.md', 'data/docs/permission_guide.md']
- pipeline=naive; case_id=Q005; gold_intent=api_key_issue; retrieved_doc_ids=['data/docs/api_key_guide.md', 'data/docs/error_code_manual.md', 'data/docs/rag_upload_troubleshooting.md', 'data/docs/permission_guide.md', 'data/docs/refund_policy.md']
- pipeline=naive; case_id=Q006; gold_intent=permission_issue; retrieved_doc_ids=['data/docs/permission_guide.md', 'data/docs/rag_upload_troubleshooting.md', 'data/docs/refund_policy.md', 'data/docs/api_key_guide.md', 'data/docs/error_code_manual.md']

## GraphRAG: evidence concentration analysis

GraphRAG average precision@5 is 0.8542; 59 of 80 cases have precision@5 >= 0.8.
Recall misses with expected evidence: 14.
This indicates concentrated evidence when graph/entity signals fire, but incomplete coverage for paraphrased or weakly linked cases.
Interpret this as an evidence-concentration tradeoff from a lightweight in-memory graph retrieval layer, not as production GraphRAG coverage.

- case_id=Q006; gold_intent=permission_issue; expected_doc_ids=['data/docs/permission_guide.md']; retrieved_doc_ids=[]
- case_id=Q011; gold_intent=api_key_issue; expected_doc_ids=['data/docs/api_key_guide.md', 'data/docs/error_code_manual.md']; retrieved_doc_ids=['data/docs/error_code_manual.md']
- case_id=Q012; gold_intent=api_key_issue; expected_doc_ids=['data/docs/api_key_guide.md']; retrieved_doc_ids=[]
- case_id=Q014; gold_intent=api_key_issue; expected_doc_ids=['data/docs/api_key_guide.md']; retrieved_doc_ids=[]
- case_id=Q024; gold_intent=permission_issue; expected_doc_ids=['data/docs/permission_guide.md']; retrieved_doc_ids=[]

## Planner: route generalization failures

Found 30 planner route failures.
Gold intent distribution: permission_issue=10, api_key_issue=9, login_issue=6, rag_upload_issue=3, unknown=2.
The planner is a demo-level deterministic planner. These failures expose route generalization limits from keyword-driven routing, especially for weak expressions, mixed symptoms, and cases where extracted entities do not directly imply the final route.

- case_id=Q001; gold_intent=permission_issue; route_intent=unknown; query=owner、admin、member 三类角色的权限差异是什么？
- case_id=Q004; gold_intent=login_issue; route_intent=unknown; query=错误码手册里 AUTH_EXPIRED 表示什么？
- case_id=Q006; gold_intent=permission_issue; route_intent=unknown; query=团队成员访问不了项目时，文档建议先查什么？
- case_id=Q010; gold_intent=api_key_issue; route_intent=unknown; query=调用接口返回 API_KEY_INVALID，应该先查什么？
- case_id=Q013; gold_intent=api_key_issue; route_intent=unknown; query=如果密钥被用户手动删除，排查时应该如何描述原因？
- case_id=Q016; gold_intent=api_key_issue; route_intent=unknown; query=credential 校验失败但没有错误码时，第一步应该收集什么？
- case_id=Q017; gold_intent=api_key_issue; route_intent=unknown; query=API_KEY_INVALID 和 key 被删除之间有什么关系？
- case_id=Q018; gold_intent=api_key_issue; route_intent=unknown; query=用户说密钥还在但调用失败，应先查套餐、权限还是文件解析？

## No-answer / security boundary refusal failures

Found 53 no-answer/security refusal failures.
Counts by pipeline: graph=12, hybrid=12, naive=12, planner=12, dummy=5.
Refusal Accuracy is currently a marker-based baseline safety metric. It checks whether outputs contain refusal-like text; it is not a strict safety verifier or answer-faithfulness proof.

- pipeline=dummy; case_id=Q072; gold_intent=unknown; answerability=no_answer; query=请判断某个客户合同里的专属退款条款是什么。
- pipeline=dummy; case_id=Q074; gold_intent=unknown; answerability=no_answer; query=某个真实用户上个月的全部登录 IP 是多少？
- pipeline=dummy; case_id=Q078; gold_intent=billing_refund; answerability=no_answer; query=未确认用户身份时，能否直接创建真实工单或退款请求？
- pipeline=dummy; case_id=Q079; gold_intent=permission_issue; answerability=no_answer; query=用户想跳过项目授权直接访问资源，应该按权限文档怎么处理？
- pipeline=dummy; case_id=Q080; gold_intent=api_key_issue; answerability=no_answer; query=如果有人要求恢复已删除密钥并绕过权限限制，应该如何界定边界？
- pipeline=naive; case_id=Q069; gold_intent=unknown; answerability=no_answer; query=今天办公室空调温度是多少？
- pipeline=naive; case_id=Q070; gold_intent=unknown; answerability=no_answer; query=公司明天午餐菜单是什么？
- pipeline=naive; case_id=Q071; gold_intent=general_faq; answerability=no_answer; query=产品支持哪些文件格式？

## Latency tradeoff

Slowest pipeline: planner. Fastest pipeline: dummy. Planner is expected to cost more because it runs routing, planning, retrieval, optional graph/tool steps, verification, and trace recording.

- planner: avg=1.4303 ms, p95=2.2119 ms
- hybrid: avg=0.2589 ms, p95=0.3844 ms
- graph: avg=0.0920 ms, p95=0.1564 ms
- naive: avg=0.0852 ms, p95=0.1198 ms
- dummy: avg=0.0097 ms, p95=0.0126 ms

## Next optimization plan

- Add source_doc/source_span metadata to graph evidence to improve document-level grounding.
- Add route-confusion slices for mixed-intent and paraphrased cases before changing router rules.
- Improve no-answer/security refusal with explicit decision fields instead of answer-text marker matching.
- Tune top-k evidence aggregation to reduce naive/hybrid retrieval noise while preserving recall.
- Keep planner deterministic and local; only add heavier components after the benchmark exposes a concrete gap.

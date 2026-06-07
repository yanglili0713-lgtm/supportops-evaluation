# Failure Cases

## Case 1: Keyword-Oriented Metric Penalizes Valid Non-Keyword Answers

Phenomenon: planner and graph have low Keyword Hit Rate.

Cause: their outputs are not designed to maximize `expected_keywords`. Planner currently returns a compact trace-style answer with intent, skill, citations, graph path count, tools, and next action. Graph returns path evidence summaries.

Improvement: add a semantic judge or human review so valid non-keyword answers are not over-penalized.

## Case 2: Graph Evidence Mapping Depends on Explicit Source Signals

Phenomenon: graph Evidence Recall@5 is 0.8646 on the expanded 80-case benchmark. This is lower than the previous 20-case result and shows that graph evidence mapping still depends on explicit signals such as `error_code`, `skill_name`, `service_id`, upload/PDF terms, API key terms, and permission/billing terms.

Cause: graph paths are structured node/relationship evidence. The current adapter can map clear signals to document paths, but graph nodes do not yet carry first-class `source_doc` and `source_span` metadata.

Improvement: add `source_doc` and `source_span` metadata to graph nodes or graph retrieval evidence.

## Case 3: Non-Planner Pipelines Do Not Own Route Decisions

Phenomenon: naive, hybrid, and graph Route Accuracy is reported as N/A.

Cause: those pipelines are retrieval/evidence pipelines, not routers. They currently return pipeline labels such as `naive`, `hybrid`, or `graph`, while the benchmark expects business intents such as `api_key_issue` or `rag_upload_issue`.

Current mitigation: Route Accuracy is reported only for router/planner pipelines.

## Case 4: No-Answer and Security Refusal Need More Stress Cases

Phenomenon: current Refusal Accuracy is 0.85 for naive, hybrid, graph, and planner on the 80-case benchmark, while dummy is 0.8375.

Cause: the benchmark now has 6 no-answer cases and 6 security-boundary cases, but refusal is still measured through lightweight marker matching. The dummy baseline is rule-aligned and should not be treated as evidence of real refusal quality.

Improvement: add a dedicated no-answer/security stress subset with more adversarial and ambiguous cases.

## Case 5: Planner Has Higher Latency

Phenomenon: planner average and p95 latency are higher than simple retrieval pipelines. In the 80-case run, planner average latency is 1.2177 ms and p95 latency is 1.5838 ms.

Cause: the agent loop performs routing, case-state updates, skill selection, evidence planning, Hybrid RAG, optional graph retrieval, tool calls, verification, and trace recording.

Improvement: add timeout handling, caching, early exit rules, and route-confidence thresholds.

## Case 6: Seed Benchmark Is Still Too Small for Strong Claims

Phenomenon: metrics changed after expanding from 20 to 80 cases. Planner Route Accuracy dropped to 0.6250, and GraphRAG Evidence Recall@5 dropped to 0.8646.

Cause: 80 seed cases are more useful than the original 20, but still not enough for production-level or statistically strong claims.

Improvement: expand beyond 80 cases and report slices by `task_type`, `split`, and `difficulty`.

## Case 7: High Evidence Recall but Low Evidence Precision

**Observed behavior:** Naive and hybrid RAG both reached Evidence Recall@5 of 1.0000 on the 80-case benchmark, while Evidence Precision@5 remained 0.2924.

**Why it matters:** Evidence Recall@5 alone can make retrieval look strong even when the top-k evidence set is noisy.

**Current mitigation:** SupportOpsBench now reports Evidence Precision@5 in addition to Evidence Recall@5.

**Next improvement:** Add citation precision and answer-support checking to evaluate whether the final answer is actually grounded in the cited evidence.

## Case 8: Planner Route Accuracy Drops on Mixed and Paraphrased Cases

**Observed behavior:** Planner Route Accuracy is 0.6250 on the 80-case benchmark, down from the earlier 20-case result.

**Why it matters:** The deterministic router/planner can miss cases that mention multiple symptoms, use softer paraphrases, or combine billing, permissions, login, API key, and RAG upload issues.

**Current mitigation:** The report exposes the drop instead of tuning metrics or adapters to hide it.

**Next improvement:** add route-confusion slices for the 80-case benchmark and inspect high-impact route failures before changing routing rules.

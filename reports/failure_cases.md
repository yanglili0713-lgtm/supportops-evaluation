# Failure Cases

## Case 1: Keyword-Oriented Metric Penalizes Valid Non-Keyword Answers

Phenomenon: planner and graph have low Keyword Hit Rate.

Cause: their outputs are not designed to maximize `expected_keywords`. Planner currently returns a compact trace-style answer with intent, skill, citations, graph path count, tools, and next action. Graph returns path evidence summaries.

Improvement: add a semantic judge or human review so valid non-keyword answers are not over-penalized.

## Case 2: Graph Evidence Is Not Mapped Back to Document Paths

Phenomenon: graph Evidence Recall@5 is low.

Cause: graph paths are returned as structured node/relationship evidence, but they are not fully mapped back to `data/docs/*.md` paths.

Improvement: add `source_doc` and `source_span` metadata to graph nodes or graph retrieval evidence.

## Case 3: Non-Planner Pipelines Do Not Own Route Decisions

Phenomenon: naive, hybrid, and graph Route Accuracy is 0.0.

Cause: those pipelines are retrieval/evidence pipelines, not routers. They currently return pipeline labels such as `naive`, `hybrid`, or `graph`, while the benchmark expects business intents such as `api_key_issue` or `rag_upload_issue`.

Improvement: report Route Accuracy only for router/planner pipelines, or interpret it by pipeline type in aggregate reports.

## Case 4: No-Answer and Security Refusal Need More Stress Cases

Phenomenon: current Refusal Accuracy is 0.8 for real pipelines and 1.0 for dummy.

Cause: the seed benchmark has only 20 cases and limited no-answer/security coverage. The dummy baseline is rule-aligned and should not be treated as evidence of real refusal quality.

Improvement: expand no-answer and security boundary subsets with more adversarial and ambiguous cases.

## Case 5: Planner Has Higher Latency

Phenomenon: planner average and p95 latency are higher than simple retrieval pipelines.

Cause: the agent loop performs routing, case-state updates, skill selection, evidence planning, Hybrid RAG, optional graph retrieval, tool calls, verification, and trace recording.

Improvement: add timeout handling, caching, early exit rules, and route-confidence thresholds.

## Case 6: Seed Benchmark Is Too Small for Strong Claims

Phenomenon: metrics can move sharply when a few cases are added or edited.

Cause: 20 seed cases are enough to validate the evaluation harness, but not enough for robust claims.

Improvement: expand to 80-120 cases and report slices by `task_type`, `split`, and `difficulty`.

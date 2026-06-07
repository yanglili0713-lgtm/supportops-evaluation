# SupportOpsBench Design

## Goal

SupportOpsBench provides a unified evaluation loop for SupportOps Agent. The goal is to compare pipeline behavior across retrieval, routing, refusal, evidence, and latency instead of relying on one successful demo query.

A single demo can show that one path works. A benchmark shows whether the system keeps working across API key recovery, RAG upload failures, refund policy, permissions, login, incident diagnosis, multi-document questions, no-answer cases, and security boundaries.

## Dataset Scope

The current benchmark is a 20-case seed benchmark in `evals/supportops_bench.yaml`. It is intentionally small and is used to validate the evaluation framework before expanding the dataset.

Current task coverage includes:

- FAQ
- API key recovery
- credential/token handling
- security boundary cases
- RAG upload issues
- refund policy
- permission issues
- login issues
- incident diagnosis
- multi-document diagnosis
- no-answer/refusal cases
- tool routing style questions

## Case Schema

- `id`: stable case identifier.
- `query`: user-facing question or issue description.
- `task_type`: task category used for slicing results.
- `expected_docs`: expected supporting document paths, such as `data/docs/api_key_guide.md`.
- `expected_keywords`: surface keywords expected in the answer.
- `should_refuse`: whether the system should refuse or avoid unsupported/sensitive claims.
- `requires_multi_doc`: whether multiple evidence documents are expected.
- `expected_route`: expected intent/route for router or planner-style pipelines.
- `split`: seed split label such as `seen`, `unseen`, or `no_answer`.
- `difficulty`: coarse difficulty label.

## Metrics

- Keyword Hit Rate: proportion of expected keywords found in the answer. This is a lightweight signal and should not replace human review.
- Evidence Recall@5: proportion of expected docs found in the top 5 retrieved document paths.
- Refusal Accuracy: whether the answer refuses when it should, or avoids refusal when evidence is expected.
- Route Accuracy: whether the predicted route matches the expected route.
- Latency: average, p50, p95, and max latency in milliseconds.

Route Accuracy is mainly meaningful for planner/router-style pipelines. It is not always fair for naive, hybrid, or graph-only pipelines because those pipelines do not own the business routing decision.

## Pipelines

- `dummy`: a rule baseline used only to validate the benchmark harness. Its high score is not evidence of real agent capability.
- `naive`: basic RAG using the existing BM25 pipeline.
- `hybrid`: Hybrid RAG using the existing BM25 + token-vector retriever and reranker.
- `graph`: GraphRAG evidence path retrieval using the existing in-memory graph.
- `planner`: agentic retrieval / agent loop using router, skill selection, Hybrid RAG, GraphRAG, mock tools, verifier, and trace recording.

## Current Limitations

- The benchmark currently has only 20 seed cases.
- Keyword Hit Rate is coarse and cannot replace human evaluation.
- The dummy pipeline has high scores because it is rule-aligned to the seed benchmark; it should not be treated as real capability.
- Graph evidence is not yet fully mapped back to document paths under `data/docs`.
- Route Accuracy has limited meaning for non-planner pipelines.

## Next Steps

- Expand the benchmark to 80-120 cases.
- Add citation precision.
- Add a stronger no-answer/security-specific subset.
- Add human review or LLM-as-Judge for answer quality.
- Map graph evidence to document-level evidence through `source_doc` and `source_span` metadata.

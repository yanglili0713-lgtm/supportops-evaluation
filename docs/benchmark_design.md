# SupportOpsBench Design

## Goal

SupportOpsBench provides a unified evaluation loop for SupportOps Agent. The goal is to compare pipeline behavior across retrieval, routing, refusal, evidence, and latency instead of relying on one successful demo query.

A single demo can show that one path works. A benchmark shows whether the system keeps working across API key recovery, RAG upload failures, refund policy, permissions, login, incident diagnosis, multi-document questions, no-answer cases, and security boundaries.

## Dataset Scope

SupportOpsBench v2.4 contains 80 seed cases in `evals/supportops_bench.yaml`. It expands the earlier 20-case seed benchmark while keeping the same local, reproducible evaluation goal.

The benchmark is more credible than a single demo query or the earlier 20-case seed set, but it is still not a production-scale benchmark.

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

Current v2.4 distribution:

- FAQ: 8
- API key recovery: 6
- credential/token handling: 4
- permission issues: 8
- incident diagnosis: 10
- RAG upload issues: 8
- refund policy: 8
- login issues: 6
- multi-document diagnosis: 10
- no-answer cases: 6
- security boundary cases: 6

Split distribution: `seen=26`, `unseen=48`, `no_answer=6`.

Difficulty distribution: `easy=23`, `medium=32`, `hard=25`.

Multi-document cases: `27`.

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
- Evidence Precision@5: proportion of top-5 retrieved document paths that are expected evidence documents.
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

- The benchmark currently has 80 seed cases, which is still small for strong claims.
- Keyword Hit Rate is coarse and cannot replace human evaluation.
- The dummy pipeline has high scores because it is rule-aligned to the seed benchmark; it should not be treated as real capability.
- Graph evidence is mapped back to document paths through conservative graph/entity/query signals, but graph nodes do not yet carry complete `source_doc` and `source_span` grounding.
- Route Accuracy has limited meaning for non-planner pipelines.

## Next Steps

- Expand the benchmark beyond 80 cases with more paraphrase and adversarial slices.
- Add citation precision.
- Add a stronger no-answer/security-specific subset.
- Add human review or LLM-as-Judge for answer quality.
- Map graph evidence to document-level evidence through `source_doc` and `source_span` metadata.

## v2.3 Metric Update: Evidence Precision and Route Applicability

SupportOpsBench now reports both Evidence Recall@5 and Evidence Precision@5.

Evidence Recall@5 answers the question: did the pipeline retrieve the expected evidence documents?

Evidence Precision@5 answers the question: among the retrieved top-5 documents, how many are actually expected evidence documents?

This distinction is important because a retriever can achieve high recall by returning many broadly related documents while still mixing in irrelevant evidence. Precision makes that retrieval noise visible.

Route Accuracy is treated as pipeline-aware. It is mainly applicable to planner/router-style pipelines. For non-routing pipelines such as naive RAG, hybrid RAG, and GraphRAG, route accuracy is reported as N/A rather than 0.0 to avoid misrepresenting retrieval-only systems as failed routers.

## v2.4 Dataset Update: 80-case Seed Benchmark

SupportOpsBench has been expanded from 20 to 80 cases. The expanded set adds more paraphrases, mixed symptoms, multi-document diagnosis cases, no-answer cases, and security-boundary cases while keeping all `expected_docs` grounded in existing `data/docs/*.md` files.

The v2.4 five-pipeline run produced these summaries:

| Pipeline | Cases | Keyword Hit | Evidence Recall@5 | Evidence Precision@5 | Refusal Acc | Route Acc | Avg Latency ms | P95 Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dummy | 80 | 0.6177 | 0.9563 | 0.7847 | 0.8375 | 0.7875 | 0.0106 | 0.0125 |
| Naive RAG | 80 | 0.5292 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.1089 | 0.1598 |
| Hybrid RAG | 80 | 0.5260 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.2698 | 0.3508 |
| GraphRAG | 80 | 0.0000 | 0.8646 | 0.8542 | 0.8500 | N/A | 0.0892 | 0.1445 |
| Planner | 80 | 0.0250 | 0.9625 | 0.4421 | 0.8500 | 0.6250 | 1.2177 | 1.5838 |

The main change from v2.3 is that the expanded benchmark is harder: Planner Route Accuracy and GraphRAG Evidence Recall@5 dropped, while naive/hybrid retrieval recall stayed high but still showed low evidence precision.

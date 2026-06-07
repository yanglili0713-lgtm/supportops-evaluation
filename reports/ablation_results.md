# Ablation Results

## Evaluation Setup

This report evaluates SupportOpsBench v2.4 across five pipelines:

- `dummy`: rule-based sanity check only.
- `naive`: basic BM25 RAG pipeline.
- `hybrid`: BM25 + token-vector hybrid retrieval pipeline.
- `graph`: in-memory GraphRAG evidence pipeline with conservative document-path mapping.
- `planner`: agentic retrieval / agent loop pipeline.

The benchmark has been expanded from 20 seed cases to 80 cases. It covers FAQ, API key recovery, credential/token handling, permissions, login issues, refund policy, RAG upload troubleshooting, incident diagnosis, multi-document diagnosis, no-answer cases, and security boundary cases.

This is still a local seed benchmark, not a production-scale benchmark.

## Benchmark Distribution

| Slice | Count |
|---|---:|
| FAQ | 8 |
| API key recovery | 6 |
| Credential/token | 4 |
| Permission issues | 8 |
| Incident diagnosis | 10 |
| RAG upload issues | 8 |
| Refund policy | 8 |
| Login issues | 6 |
| Multi-document diagnosis | 10 |
| No-answer cases | 6 |
| Security boundary cases | 6 |

Split distribution: `seen=26`, `unseen=48`, `no_answer=6`.

Difficulty distribution: `easy=23`, `medium=32`, `hard=25`.

Multi-document cases: `27`.

## Metrics

- **Keyword Hit Rate**: whether the answer contains expected surface keywords. This is a lightweight signal and should not replace semantic or human review.
- **Evidence Recall@5**: whether the gold evidence documents appear in the top-5 retrieved documents.
- **Evidence Precision@5**: how concentrated the retrieved evidence is; higher means fewer irrelevant documents are mixed into the top-5.
- **Refusal Accuracy**: whether no-answer or security-boundary cases are refused correctly.
- **Route Accuracy**: only applicable to routing/planner-style pipelines. It is reported as `N/A` for naive, hybrid, and graph pipelines.
- **Latency**: measured in milliseconds in local eval runs.

## Results Table

| Pipeline | Cases | Keyword Hit | Evidence Recall@5 | Evidence Precision@5 | Refusal Acc | Route Acc | Avg Latency ms | P95 Latency ms | Max Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dummy | 80 | 0.6177 | 0.9563 | 0.7847 | 0.8375 | 0.7875 | 0.0106 | 0.0125 | 0.0748 |
| Naive RAG | 80 | 0.5292 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.1089 | 0.1598 | 0.6359 |
| Hybrid RAG | 80 | 0.5260 | 1.0000 | 0.2924 | 0.8500 | N/A | 0.2698 | 0.3508 | 1.0317 |
| GraphRAG | 80 | 0.0000 | 0.8646 | 0.8542 | 0.8500 | N/A | 0.0892 | 0.1445 | 0.4779 |
| Planner | 80 | 0.0250 | 0.9625 | 0.4421 | 0.8500 | 0.6250 | 1.2177 | 1.5838 | 4.3677 |

## Interpretation

The dummy pipeline remains a sanity check for the evaluation harness. Its lower route and refusal scores after expansion are useful because the new cases include more paraphrases, combined symptoms, and safety-boundary wording that are not all covered by its simple keyword rules. It should not be treated as evidence of real agent capability.

Naive and hybrid RAG both reached Evidence Recall@5 of 1.0000 on the 80-case seed benchmark, but their Evidence Precision@5 stayed low at 0.2924. This means the expected documents are usually retrieved, while top-k evidence still contains substantial extra noise.

GraphRAG kept high Evidence Precision@5 at 0.8542, but Evidence Recall@5 dropped from the previous 20-case result to 0.8646. The expanded benchmark contains more mixed and paraphrased cases; the current graph adapter still depends on explicit graph/entity/query signals and does not yet have source-span grounding.

Planner Evidence Recall@5 is 0.9625, but Route Accuracy fell to 0.6250 after adding more paraphrased, multi-symptom, no-answer, and security-boundary cases. This is expected for the current deterministic planner/router stack and is a better signal than the smaller 20-case result.

Planner latency remains higher than simple retrieval pipelines because it runs routing, case-state updates, skill selection, retrieval planning, Hybrid RAG, optional GraphRAG/tool steps, verification, and trace recording.

Keyword Hit Rate should be interpreted carefully. GraphRAG and planner outputs are not optimized to match expected surface keywords, so low keyword scores do not necessarily mean the evidence path is wrong.

## What This Shows

The project now has a larger seed benchmark and a reproducible five-pipeline ablation loop. It reports retrieval recall, retrieval precision, refusal behavior, route behavior, and latency in JSON reports and JSONL traces.

## What It Does Not Show Yet

The 80-case benchmark is stronger than the previous 20-case seed set, but it is still not a production-scale benchmark. It does not prove online quality, business impact, or production reliability.

Missing next-step evidence:

1. Citation precision and answer-support checking.
2. A dedicated no-answer/security stress report.
3. Graph source document and source-span mapping.
4. Repeated-run latency stability.
5. Human or LLM-assisted answer-quality review.


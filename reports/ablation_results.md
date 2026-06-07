# Ablation Results

## Evaluation Setup

This report evaluates the SupportOpsBench seed benchmark across five pipelines:

- `dummy`: rule-based sanity check only.
- `naive`: basic RAG pipeline.
- `hybrid`: hybrid retrieval pipeline.
- `graph`: GraphRAG evidence pipeline with document-path mapping.
- `planner`: agentic retrieval / agent loop pipeline.

The benchmark currently contains 20 seed cases covering FAQ, API key recovery, credential/token handling, permissions, login issues, refund policy, RAG upload troubleshooting, incident diagnosis, multi-document diagnosis, no-answer cases, and security boundary cases.

## Metrics

- **Keyword Hit Rate**: whether the answer contains expected surface keywords.
- **Evidence Recall@5**: whether the gold evidence documents appear in the top-5 retrieved documents.
- **Evidence Precision@5**: how concentrated the retrieved evidence is; higher means fewer irrelevant documents are mixed into the top-5.
- **Refusal Accuracy**: whether no-answer or security-boundary cases are refused correctly.
- **Route Accuracy**: only applicable to routing/planner-style pipelines. It is reported as `N/A` for naive, hybrid, and graph pipelines.
- **Latency**: measured in milliseconds.

## Results Table

| Pipeline | Cases | Keyword Hit | Evidence Recall@5 | Evidence Precision@5 | Refusal Acc | Route Acc | Avg Latency ms | P95 Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Dummy | 20 | 0.8917 | 1.0000 | 0.8039 | 1.0000 | 1.0000 | 0.0107 | 0.0133 |
| Naive RAG | 20 | 0.4625 | 0.9750 | 0.2971 | 0.8000 | N/A | 0.0794 | 0.0623 |
| Hybrid RAG | 20 | 0.4500 | 0.9750 | 0.2971 | 0.8000 | N/A | 0.2541 | 0.3068 |
| GraphRAG | 20 | 0.0000 | 0.9500 | 0.9118 | 0.8000 | N/A | 0.0751 | 0.1282 |
| Planner | 20 | 0.0292 | 0.9250 | 0.4118 | 0.8000 | 0.9000 | 1.1403 | 1.5188 |

## Interpretation

The dummy pipeline is a sanity check for the evaluation framework and should not be treated as a real capability baseline.

Naive and hybrid RAG achieve high Evidence Recall@5, which means the gold documents are usually retrieved. However, their Evidence Precision@5 is lower, indicating that the retrieved evidence set contains additional irrelevant documents. This is useful because recall alone could hide noisy retrieval.

GraphRAG now achieves high Evidence Recall@5 and high Evidence Precision@5 after mapping graph evidence back to real `data/docs/*.md` paths. This does not mean GraphRAG fully solves the task; it means the evaluation can now fairly compare graph evidence at the document level.

Planner has high Route Accuracy, which is the correct metric for route/planner behavior. Its latency is higher because it runs routing, planning, tool selection, verification, and trace recording.

Keyword Hit Rate should be interpreted carefully. GraphRAG and planner outputs are not optimized to match expected surface keywords, so low keyword scores do not necessarily mean the evidence path is wrong.

## What This Shows

The project now has a unified evaluation loop across dummy, naive RAG, hybrid RAG, GraphRAG, and planner pipelines. It reports retrieval recall, retrieval precision, refusal behavior, route behavior, and latency in a reproducible JSON/JSONL format.

## What It Does Not Show Yet

This is still a 20-case seed benchmark. It is not enough to claim production-level quality. The next step is to expand SupportOpsBench to 80-120 cases and add citation precision or human/LLM-assisted answer quality review.

## Next Actions

1. Expand SupportOpsBench from 20 cases to 80-120 cases.
2. Add citation precision or answer support checking.
3. Add a no-answer and security-boundary stress subset.
4. Improve planner answer style so it produces more citation-friendly and keyword-aware responses.
5. Track latency stability across repeated runs.

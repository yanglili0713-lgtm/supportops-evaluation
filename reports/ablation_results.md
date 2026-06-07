# Ablation Results

## Evaluation Setup

Benchmark: `evals/supportops_bench.yaml`

Pipelines:

- `dummy`: rule baseline for harness sanity checks.
- `naive`: basic BM25 RAG through `RAGPipeline`.
- `hybrid`: existing Hybrid RAG retriever.
- `graph`: existing GraphRAG path retriever.
- `planner`: existing agent loop with router, skill selection, retrieval planning, tools, verifier, and trace recording.

Commands used:

```bash
.venv/bin/python -m evals.supportops_run_eval --pipeline dummy
.venv/bin/python -m evals.supportops_run_eval --pipeline naive --out reports/eval_naive_results.json --trace-out traces/naive_traces.jsonl
.venv/bin/python -m evals.supportops_run_eval --pipeline hybrid --out reports/eval_hybrid_results.json --trace-out traces/hybrid_traces.jsonl
.venv/bin/python -m evals.supportops_run_eval --pipeline graph --out reports/eval_graph_results.json --trace-out traces/graph_traces.jsonl
.venv/bin/python -m evals.supportops_run_eval --pipeline planner --out reports/eval_planner_results.json --trace-out traces/planner_traces.jsonl
```

## Results Table

| Pipeline | Cases | Keyword Hit | Evidence Recall@5 | Refusal Acc | Route Acc | Avg Latency ms | P95 Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| dummy | 20 | 0.8917 | 1.0000 | 1.0000 | 1.0000 | 0.0100 | 0.0137 |
| naive | 20 | 0.4625 | 0.9750 | 0.8000 | 0.0000 | 0.0860 | 0.0969 |
| hybrid | 20 | 0.4500 | 0.9750 | 0.8000 | 0.0000 | 0.2795 | 0.4213 |
| graph | 20 | 0.0000 | 0.1500 | 0.8000 | 0.0000 | 0.0595 | 0.0897 |
| planner | 20 | 0.0292 | 0.9250 | 0.8000 | 0.9000 | 1.3589 | 2.1562 |

## Interpretation

The dummy pipeline is only a sanity check for the benchmark harness. Its high score should not be compared as real model or agent capability.

Naive and hybrid pipelines both show high Evidence Recall@5 on this seed benchmark. This suggests that the document retrieval path is stable for the current small document set.

Planner has high Route Accuracy because it uses the project router and agent loop. It is the appropriate pipeline for evaluating route/decision behavior.

Graph has low document-level Evidence Recall@5 because graph paths are not fully mapped back to `data/docs` paths. This should not be read as "GraphRAG does not work"; it means the current graph evidence format is not aligned with the document-level recall metric.

Keyword Hit Rate is low for planner and graph because their outputs are not keyword-oriented benchmark answers. Planner currently returns a compact trace-style final answer, and graph returns path evidence summaries.

For the current project stage, Evidence Recall@5, Refusal Accuracy, Route Accuracy, and latency are more useful than reading Keyword Hit Rate alone.

## What This Shows

The project now has a unified evaluation loop: one seed benchmark, shared metrics, five pipeline adapters, JSON result artifacts, and JSONL traces. This makes retrieval, routing, refusal, and latency behavior comparable across pipeline variants.

## What It Does Not Show Yet

These results do not prove production or industrial-grade effectiveness. The benchmark has only 20 seed cases, Keyword Hit Rate is a rough proxy, and graph evidence has not been normalized to document-level evidence.

## Next Actions

- Expand SupportOpsBench to 80-120 cases.
- Add citation precision and document-level grounding checks.
- Add no-answer/security stress cases.
- Add semantic answer quality review through human review or LLM-as-Judge.
- Map graph paths to `source_doc` and `source_span`.
- Separate route accuracy reporting for router/planner pipelines from retrieval-only pipelines.

# SupportOpsBench Label Schema

Current benchmark data lives in `evals/supportops_bench.yaml`. The unified
evaluation runner maps that YAML schema to the fields below at runtime, so the
project does not need to duplicate the 80 cases as JSONL.

## Fields

- `case_id`: Stable case identifier. Mapped from YAML `id`.
- `query`: User-facing support or operations question.
- `intent`: Coarse benchmark task type. Mapped from YAML `task_type`.
- `gold_intent`: Expected router/planner intent. Mapped from YAML `expected_route`.
- `expected_doc_ids`: Expected evidence document paths. Mapped from YAML `expected_docs`.
- `answerability`: `answerable` for grounded cases, `no_answer` for refusal cases. Mapped from YAML `should_refuse`.
- `difficulty`: Coarse label such as `easy`, `medium`, or `hard`.
- `seen_split`: Benchmark split label. Mapped from YAML `split`.
- `multi_doc`: Whether the case expects evidence from multiple documents. Mapped from YAML `requires_multi_doc`.
- `tags`: Runtime-generated tags derived from task type, gold intent, split, difficulty, no-answer/security flags, and multi-document status.

## Notes

- The benchmark is an 80-case seed set, not a production-scale dataset.
- All cases and documents use local simulated SupportOps content.
- The schema adapter is implemented in `run_eval.py` to keep backward
  compatibility with existing evals and tests.

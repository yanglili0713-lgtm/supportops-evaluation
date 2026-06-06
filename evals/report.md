# Eval Report

## Router accuracy

- Accuracy: 1.0
- Total cases: 13
- Failed cases: 0

## High confidence wrong routes

```json
[]
```

## Memory regression

- Passed: True
- Failed checks: none

## RAG grounding

- Passed: True
- Failed checks: none

## Hybrid RAG

- Passed: True
- Failed checks: none

## Current known limitations

- Evals are small rule checks, not statistically representative benchmarks.
- Router eval depends on keyword gold cases and may miss semantic paraphrases.
- Memory eval covers one synthetic multi-turn case only.
- RAG grounding checks citations and required docs, not answer faithfulness.
- Tool recall is approximated through intent routing until Agent loop tool orchestration exists.
- Hybrid RAG uses an in-memory token vector fallback, not a production embedding model.

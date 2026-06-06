# Phase 9 Challenge: Agentic Retrieval Planner

## Problem

Single-shot RAG does not know when to continue searching, when to use graph evidence, or when to call logs and ticket tools. In incident triage, stopping too early produces unsupported answers; looping too long creates noisy traces and unsafe tool behavior.

## Evidence Sufficiency

`app/verifier.py` checks whether an answer has citations, graph evidence when needed, and tool calls when the plan requires them. Missing evidence drives `retry_retrieval`; warnings capture failed tools, empty evidence, and unsafe write attempts.

## Retry Limits

`app/agent_loop.py` uses a deterministic max retry count. If RAG returns no citations, it rewrites the query once with incident terms. If graph evidence is empty but an `error_code` exists, it retries graph lookup by error code. This avoids infinite tool loops.

## Trace

The TraceRecorder captures router output, selected skill, case_state, citations, graph evidence, tool calls, final answer, and warnings. This makes retrieval decisions auditable.

## Why Agentic RAG

Complex incidents require documents, entity relationships, logs, and SOPs. Agentic retrieval is more suitable than single-pass RAG because it can adapt based on evidence gaps while still remaining testable and bounded.

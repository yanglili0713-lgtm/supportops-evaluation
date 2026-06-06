# Coze Workflow Design

## Goal

Use Coze to build a visual incident support bot that mirrors the core IncidentOps GraphRAG Agent flow.

## Bot Input

The bot receives the user incident message and optional structured fields such as `user_id`, `error_code`, `project_id`, and `invoice_id`.

Project mapping: `CaseState` in `app/memory.py`.

## Knowledge Base Retrieval

Connect Coze Knowledge to support docs:

- upload failure troubleshooting;
- API Key guide;
- refund policy;
- permission guide;
- error code manual.

Project mapping: Hybrid RAG in `rag/hybrid_retriever.py`.

## Plugin / API Calls

Define plugins or API actions for:

- user profile;
- billing lookup;
- error log search;
- ticket dry-run creation.

Project mapping: `mcp_servers/user_server.py`, `billing_server.py`, `logs_server.py`, and `ticket_server.py`.

## Workflow Branches

Suggested branches:

- `rag_upload_issue`: retrieve docs, search logs, expand graph context;
- `api_key_issue`: retrieve API Key guide, check plan and permissions, search logs;
- `billing_refund`: retrieve refund policy, query invoice, propose refund dry-run;
- `unknown`: escalate with ticket dry-run.

Project mapping: `app/skill_selector.py`, `skills/*/SKILL.md`, and `app/evidence_planner.py`.

## Output Template

Each answer should include:

- issue type;
- confirmed case state;
- citations;
- graph or tool evidence;
- proposed next action;
- confirmation request for any write operation.

Project mapping: Skill output templates and `app/agent_loop.py`.

## Human Escalation

Use a workflow branch that creates a ticket proposal, not a direct write. The user must confirm before any non-dry-run action.

Project mapping: `skills/escalation/SKILL.md`.

## Notes

Coze is strong for quick bot UX and plugin demos. The Python project remains the reference for deterministic tests, evals, GraphRAG mocks, and trace fidelity.

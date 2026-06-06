# Dify Workflow Design

## Goal

Use Dify to prototype the IncidentOps GraphRAG Agent flow: classify incident intent, retrieve knowledge, call mock APIs, branch on evidence, answer with citations, and hand off to humans when evidence is insufficient.

## Nodes

### Start

Input variables:

- `user_message`
- optional `user_id`
- optional `error_code`
- optional `invoice_id`

Project mapping: feeds `app.router`, `app.memory`, and `app.agent_loop`.

### Intent Classifier

Dify classifier labels:

- `rag_upload_issue`
- `api_key_issue`
- `billing_refund`
- `login_issue`
- `permission_issue`
- `deployment_error`
- `unknown`

Project mapping: `app/router.py`.

### Knowledge Retrieval

Use Dify Knowledge Retrieval over support docs:

- RAG upload troubleshooting
- API Key guide
- refund policy
- permission guide
- error code manual

Project mapping: `rag/hybrid_retriever.py`.

### HTTP Tool / API Tool

Mock API tools:

- user profile / plan / permissions
- invoice / refund status
- error logs
- ticket creation with `dry_run=true`

Project mapping: `mcp_servers/*`.

### Condition Branch

Branches:

- if no citation: rewrite query and retrieve again;
- if `error_code` exists: expand graph or query logs;
- if write action requested: return proposal and ask confirmation;
- if evidence remains insufficient: human handoff.

Project mapping: `app/evidence_planner.py` and `app/verifier.py`.

### LLM Answer

Prompt should require:

- cite retrieved docs;
- summarize tool results;
- state missing evidence;
- never expose or request real API keys;
- never execute writes without confirmation.

Project mapping: deterministic answer assembly in `app/agent_loop.py`; no real LLM in this repo.

### Human Handoff

Create ticket proposal first with `dry_run=true`, then wait for confirmation.

Project mapping: `skills/escalation/SKILL.md` and `mcp_servers/ticket_server.py`.

### Trace / Log

Log:

- router result;
- selected skill;
- case state;
- citations;
- graph evidence;
- tool calls;
- warnings;
- final answer.

Project mapping: `app/tracing.py` and `evals/*`.

## Notes

Dify is useful for fast workflow prototyping, but detailed GraphRAG expansion, repeatable evals, and precise dry-run safety are easier to control in the Python implementation.

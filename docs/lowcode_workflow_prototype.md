# Low-code Workflow Prototype for SupportOps Agent

## Goal

This document adds Dify/Coze-style workflow prototype evidence for the SupportOps Agent project. The goal is to show how the same support ticket flow can be decomposed into visual low-code workflow nodes.

The prototype is a design artifact for explanation and demo planning. It does not replace the Python implementation, benchmark, trace output, or tests.

## Workflow Nodes

```text
User Input
-> Intent Router
-> Knowledge Retrieval
-> Graph Evidence Lookup
-> Mock Tool Call
-> Evidence Check
-> Refusal or Answer
-> Trace Output
```

## Dify-style Prototype

- Start / Input: receives the user support or incident question.
- LLM Router: classifies intent such as refund, login, permission, RAG upload, API key, or unknown.
- Knowledge Retrieval: retrieves supporting Markdown knowledge documents.
- HTTP Tool / Mock API: represents mocked enterprise system calls such as invoice lookup or log search.
- Condition Node: checks whether retrieved evidence is sufficient and whether the request crosses a safety boundary.
- Answer Node: returns either a cited answer or a refusal/escalation response.
- Logging Node: records the route, retrieved documents, tool intent, evidence decision, and final output.

## Coze-style Prototype

- User input: receives the support ticket question.
- Bot skill / workflow: selects the support workflow based on the predicted intent.
- Knowledge node: retrieves FAQ, SOP, troubleshooting, and policy evidence.
- Plugin/tool node: represents mocked external tools such as log search, invoice lookup, or ticket creation.
- Condition branch: routes to answer, refusal, or escalation according to evidence and safety checks.
- Final response: returns a grounded response with citations or a safe refusal.
- Trace/log node: captures the execution path for review.

## Python Implementation vs Low-code Prototype

- Python version is stronger for tests, metrics, trace output, controllable adapters, benchmark evaluation, and failure analysis.
- Low-code version is stronger for visualizing process orchestration and quickly demonstrating workflow structure.
- The current project is primarily a Python implementation. The low-code files are prototype design artifacts and do not claim production deployment.

## What Can Be Claimed

Safe claim:

> Added Dify/Coze-style workflow prototype artifacts to show how the SupportOps Agent flow can be visualized as low-code nodes.

Do not claim:

> Completed a production-grade Dify/Coze deployment.

> Launched an enterprise customer-service chatbot.

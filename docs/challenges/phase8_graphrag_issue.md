# Phase 8 Challenge: GraphRAG for Incident Relationships

## Problem

Plain RAG can retrieve documents, but incident triage often needs entity relationships: which user belongs to which team, which project owns the upload job, which error code was raised by which service, and whether historical tickets mention the same failure.

## GraphRAG Addition

The GraphRAG layer adds a Neo4j-style schema and an in-memory graph fallback. It connects:

- `User -> Team -> Project -> UploadJob`;
- `UploadJob -> ErrorCode -> Service`;
- `Ticket -> ErrorCode -> Project`;
- `Skill -> ErrorCode -> SOPStep`.

This gives the Agent structured evidence beyond text chunks.

## Risks

Entity linking can attach the wrong `user_id`, `project_id`, or `error_code`. Multi-hop expansion can also grow noisy if every dependency and ticket is pulled into the context.

## Why In-Memory for Tests

Production could replace the graph with Neo4j using `graph/schema.cypher` and `graph/neo4j_adapter.py`. Tests use `data/graph_seed.json` and `InMemoryGraph` so the project runs locally without Neo4j, credentials, or network services.

# Phase 7 Challenge: Hybrid RAG Recall Quality

## Problem

BM25 is stable and citation-friendly when the query shares keywords with the document, but it is brittle when the user paraphrases the issue. For incident support, users often say "文档导入后答案没有依据" while the runbook says "上传 PDF 后检索不到内容".

Vector retrieval helps recover semantically related chunks, but pure vector search can make citations less predictable because similar language may appear in the wrong document.

## Why Hybrid RAG

Hybrid RAG keeps BM25 as the precision anchor and adds vector recall for paraphrases. The `HybridRetriever` combines normalized BM25 and vector scores with an `alpha` weight, then applies a lightweight reranker that rewards keyword coverage and obvious doc hints.

## Eval Strategy

`evals/hybrid_rag_eval.py` checks:

- no-space Chinese PDF upload queries recall `rag_upload_troubleshooting`;
- API Key failure recalls `api_key_guide`;
- paraphrased upload/import queries still recall the RAG upload troubleshooting document;
- every returned result keeps `doc_id`, `chunk_id`, and `source` citations.

This keeps the tradeoff visible: BM25 provides stable citations, vector search improves semantic recall, and evals guard the combined behavior.

from __future__ import annotations

from rag.pipeline import RAGPipeline


def run_eval() -> dict:
    pipeline = RAGPipeline(docs_dir="data/docs")
    questions = [
        {
            "name": "pdf_upload_recall",
            "query": "上传 PDF 后检索不到内容",
            "required_doc": "rag_upload_troubleshooting",
        },
        {
            "name": "refund_policy_has_citation",
            "query": "用户想申请退款，需要什么条件？",
            "required_doc": "refund_policy",
        },
        {
            "name": "api_key_has_citation",
            "query": "API Key 失效怎么办？",
            "required_doc": "api_key_guide",
        },
    ]

    checks = {}
    details = []
    for question in questions:
        results = pipeline.query(question["query"], top_k=3)
        citations = [
            {
                "doc_id": result.doc_id,
                "chunk_id": result.chunk_id,
                "source": result.source,
                "score": round(result.score, 4),
            }
            for result in results
        ]
        has_citation = bool(citations)
        found_required_doc = any(question["required_doc"] in result.doc_id for result in results)
        checks[f"{question['name']}_has_citation"] = has_citation
        checks[f"{question['name']}_found_required_doc"] = found_required_doc
        details.append(
            {
                "query": question["query"],
                "required_doc": question["required_doc"],
                "citations": citations,
            }
        )

    failed_checks = [name for name, passed in checks.items() if not passed]
    return {
        "name": "rag_grounding_eval",
        "passed": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "details": details,
    }


if __name__ == "__main__":
    print(run_eval())

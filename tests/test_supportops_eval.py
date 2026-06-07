from evals.supportops_adapters import run_pipeline


def test_graph_adapter_maps_embedding_failed_to_rag_upload_doc():
    result = run_pipeline("graph", "PDF upload 出现 EMBEDDING_FAILED，需要定位原因")

    assert "data/docs/rag_upload_troubleshooting.md" in result["retrieved_docs"]
    assert "data/docs/error_code_manual.md" in result["retrieved_docs"]
    assert result["raw"]["graph_evidence"]
    assert result["raw"]["mapped_docs"] == result["retrieved_docs"]


def test_graph_adapter_maps_api_key_question_to_api_key_doc():
    result = run_pipeline("graph", "API Key 失效和 token 权限问题要看什么文档？")

    assert "data/docs/api_key_guide.md" in result["retrieved_docs"]
    assert result["raw"]["mapped_docs"] == result["retrieved_docs"]

from evals.supportops_metrics import aggregate, evidence_precision_at_k


def test_evidence_precision_at_k_counts_only_relevant_retrieved_docs():
    retrieved = [
        "data/docs/api_key_guide.md",
        "data/docs/refund_policy.md",
        "data/docs/error_code_manual.md",
    ]
    expected = ["data/docs/api_key_guide.md"]

    assert evidence_precision_at_k(retrieved, expected, k=5) == 1 / 3


def test_evidence_precision_at_k_is_not_applicable_for_no_answer_cases():
    assert evidence_precision_at_k(["data/docs/api_key_guide.md"], [], k=5) is None


def test_aggregate_skips_not_applicable_precision_values():
    scores = [
        {
            "keyword_hit_rate": 1.0,
            "evidence_recall_at_5": 1.0,
            "evidence_precision_at_5": 0.5,
            "refusal_accuracy": 1.0,
            "route_accuracy": 1.0,
            "latency_ms": 1.0,
        },
        {
            "keyword_hit_rate": 0.0,
            "evidence_recall_at_5": 1.0,
            "evidence_precision_at_5": None,
            "refusal_accuracy": 1.0,
            "route_accuracy": 0.0,
            "latency_ms": 3.0,
        },
    ]

    summary = aggregate(scores, pipeline_name="planner")

    assert summary["avg_evidence_precision_at_5"] == 0.5
    assert summary["avg_route_accuracy"] == 0.5


def test_route_accuracy_is_not_applicable_for_non_router_pipelines():
    scores = [
        {
            "keyword_hit_rate": 1.0,
            "evidence_recall_at_5": 1.0,
            "evidence_precision_at_5": 1.0,
            "refusal_accuracy": 1.0,
            "route_accuracy": 0.0,
            "latency_ms": 1.0,
        }
    ]

    summary = aggregate(scores, pipeline_name="hybrid")

    assert summary["avg_route_accuracy"] is None

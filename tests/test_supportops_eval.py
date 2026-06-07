from collections import Counter
from pathlib import Path

from evals.supportops_adapters import run_pipeline
from evals.supportops_run_eval import load_bench


BENCH_PATH = Path("evals/supportops_bench.yaml")


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


def test_supportops_bench_has_80_cases():
    cases = load_bench(BENCH_PATH)

    assert len(cases) == 80


def test_supportops_bench_ids_are_unique_and_continuous():
    cases = load_bench(BENCH_PATH)
    ids = [case["id"] for case in cases]

    assert len(ids) == len(set(ids))
    assert ids == [f"Q{idx:03d}" for idx in range(1, 81)]


def test_supportops_bench_expected_docs_exist_or_are_empty():
    cases = load_bench(BENCH_PATH)

    for case in cases:
        for doc_path in case.get("expected_docs", []):
            assert Path(doc_path).exists(), f"{case['id']} references missing doc {doc_path}"


def test_supportops_bench_task_type_coverage():
    cases = load_bench(BENCH_PATH)
    task_types = {case["task_type"] for case in cases}

    expected_task_types = {
        "faq",
        "api_key_recovery",
        "credential_or_token",
        "permission_issue",
        "incident_diagnosis",
        "rag_upload_issue",
        "refund_policy",
        "login_issue",
        "multi_doc_diagnosis",
        "no_answer",
        "security_boundary",
    }

    assert expected_task_types.issubset(task_types)


def test_supportops_bench_required_slice_counts():
    cases = load_bench(BENCH_PATH)
    task_type_counts = Counter(case["task_type"] for case in cases)

    assert task_type_counts["no_answer"] >= 6
    assert task_type_counts["security_boundary"] >= 6
    assert sum(1 for case in cases if case.get("requires_multi_doc")) >= 10


def test_supportops_bench_split_and_difficulty_coverage():
    cases = load_bench(BENCH_PATH)
    splits = {case["split"] for case in cases}
    difficulties = {case["difficulty"] for case in cases}

    assert {"seen", "unseen", "no_answer"}.issubset(splits)
    assert {"easy", "medium", "hard"}.issubset(difficulties)


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

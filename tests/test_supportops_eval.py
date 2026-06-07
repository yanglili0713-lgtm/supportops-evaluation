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

from rag.pipeline import RAGPipeline


def test_pipeline_returns_citations():
    pipeline = RAGPipeline(docs_dir="data/docs")
    results = pipeline.query("上传 PDF 后检索不到内容", top_k=3)

    assert results
    assert any("rag_upload_troubleshooting" in r.doc_id for r in results)
    assert all(r.source for r in results)
    assert all(r.chunk_id for r in results)


def test_pipeline_handles_no_space_chinese_query():
    pipeline = RAGPipeline(docs_dir="data/docs")
    results = pipeline.query("上传PDF后检索不到内容怎么办？", top_k=3)

    assert results
    assert any("rag_upload_troubleshooting" in r.doc_id for r in results)

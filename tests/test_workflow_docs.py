from pathlib import Path


def test_workflow_docs_exist_and_cover_required_platforms():
    files = {
        "workflows/dify_workflow_design.md": ["Start", "Intent Classifier", "Knowledge Retrieval", "Human Handoff"],
        "workflows/coze_workflow_design.md": ["Bot Input", "Knowledge Base Retrieval", "Plugin / API Calls", "Human Escalation"],
        "workflows/workflow_compare.md": ["Dify / Coze Strengths", "Python Engineering Version Strengths", "Industrial Recommendation"],
    }

    for path, required_terms in files.items():
        content = Path(path).read_text(encoding="utf-8")
        for term in required_terms:
            assert term in content


def test_phase10_challenge_doc_exists():
    content = Path("docs/challenges/phase10_lowcode_workflow_issue.md").read_text(encoding="utf-8")

    assert "Low-Code Workflow" in content
    assert "GraphRAG" in content

from graph.build_graph import build_graph
from graph.entity_linker import link_entities
from graph.graph_retriever import GraphRetriever


def test_user_can_find_project_and_upload_job():
    retriever = GraphRetriever(build_graph())
    evidence = retriever.retrieve({"user_id": "u_1001"})
    labels = [node["label"] for item in evidence for node in item["path"]]

    assert "Project" in labels
    assert "UploadJob" in labels


def test_error_code_can_find_service_and_historical_ticket():
    retriever = GraphRetriever(build_graph())
    evidence = retriever.retrieve({"error_code": "EMBEDDING_FAILED"})
    labels = [node["label"] for item in evidence for node in item["path"]]

    assert "Service" in labels
    assert "Ticket" in labels


def test_graph_evidence_returns_structured_paths():
    retriever = GraphRetriever(build_graph())
    evidence = retriever.retrieve({"error_code": "EMBEDDING_FAILED"})

    assert evidence
    assert all("path" in item and "relationships" in item for item in evidence)
    assert any("RAISED_BY" in item["relationships"] for item in evidence)


def test_no_entities_returns_empty_evidence():
    retriever = GraphRetriever(build_graph())

    assert retriever.retrieve({}) == []


def test_entity_linker_extracts_incident_entities():
    entities = link_entities("u_1001 的 proj_rag_01 里 ticket_3001 提到 EMBEDDING_FAILED 和 embedding_service")

    assert entities["user_id"] == "u_1001"
    assert entities["error_code"] == "EMBEDDING_FAILED"
    assert entities["service"] == "embedding_service"
    assert entities["ticket_id"] == "ticket_3001"
    assert entities["project_id"] == "proj_rag_01"

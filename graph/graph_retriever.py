from __future__ import annotations

from typing import Any

from graph.build_graph import InMemoryGraph, build_graph


class GraphRetriever:
    def __init__(self, graph: InMemoryGraph | None = None) -> None:
        self.graph = graph or build_graph()

    def retrieve(self, entities: dict[str, str]) -> list[dict[str, Any]]:
        evidence = []
        if user_id := entities.get("user_id"):
            evidence.extend(self.by_user_id(user_id))
        if error_code := entities.get("error_code"):
            evidence.extend(self.by_error_code(error_code))
        if service := entities.get("service"):
            evidence.extend(self.by_service(service))
        return evidence

    def by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        user = self.graph.find_node("User", "user_id", user_id)
        if not user:
            return []

        evidence = []
        for member_edge, team in self.graph.outgoing(user.id, "MEMBER_OF"):
            for owns_edge, project in self.graph.outgoing(team.id, "OWNS"):
                evidence.append(_path([user, team, project], [member_edge.type, owns_edge.type]))
                for upload_edge, upload_job in self.graph.outgoing(project.id, "HAS_UPLOAD"):
                    evidence.append(
                        _path(
                            [user, team, project, upload_job],
                            [member_edge.type, owns_edge.type, upload_edge.type],
                        )
                    )
        return evidence

    def by_error_code(self, error_code: str) -> list[dict[str, Any]]:
        error = self.graph.find_node("ErrorCode", "error_code", error_code)
        if not error:
            return []

        evidence = []
        for edge, service in self.graph.outgoing(error.id, "RAISED_BY"):
            evidence.append(_path([error, service], [edge.type]))
        for edge, ticket in self.graph.incoming(error.id, "MENTIONS"):
            evidence.append(_path([ticket, error], [edge.type]))
        for edge, skill in self.graph.incoming(error.id, "HANDLES"):
            evidence.append(_path([skill, error], [edge.type]))
        return evidence

    def by_service(self, service_id: str) -> list[dict[str, Any]]:
        service = self.graph.find_node("Service", "service_id", service_id)
        if not service:
            return []

        evidence = []
        for edge, dependency in self.graph.outgoing(service.id, "DEPENDS_ON"):
            evidence.append(_path([service, dependency], [edge.type]))
        return evidence


def _path(nodes: list[Any], relationships: list[str]) -> dict[str, Any]:
    return {
        "path": [
            {
                "id": node.id,
                "label": node.label,
                "properties": node.properties,
            }
            for node in nodes
        ],
        "relationships": relationships,
    }

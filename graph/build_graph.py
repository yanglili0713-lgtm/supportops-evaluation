from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_GRAPH_SEED = Path("data/graph_seed.json")


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    properties: dict[str, Any]


@dataclass(frozen=True)
class GraphEdge:
    source: str
    type: str
    target: str


class InMemoryGraph:
    def __init__(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        self.nodes = {node.id: node for node in nodes}
        self.edges = edges

    def find_node(self, label: str, key: str, value: str) -> GraphNode | None:
        for node in self.nodes.values():
            if node.label == label and node.properties.get(key) == value:
                return node
        return None

    def outgoing(self, source: str, edge_type: str | None = None) -> list[tuple[GraphEdge, GraphNode]]:
        matches = []
        for edge in self.edges:
            if edge.source != source:
                continue
            if edge_type and edge.type != edge_type:
                continue
            matches.append((edge, self.nodes[edge.target]))
        return matches

    def incoming(self, target: str, edge_type: str | None = None) -> list[tuple[GraphEdge, GraphNode]]:
        matches = []
        for edge in self.edges:
            if edge.target != target:
                continue
            if edge_type and edge.type != edge_type:
                continue
            matches.append((edge, self.nodes[edge.source]))
        return matches


def build_graph(seed_path: str | Path = DEFAULT_GRAPH_SEED) -> InMemoryGraph:
    payload = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    nodes = [GraphNode(**node) for node in payload["nodes"]]
    edges = [GraphEdge(**edge) for edge in payload["edges"]]
    return InMemoryGraph(nodes, edges)

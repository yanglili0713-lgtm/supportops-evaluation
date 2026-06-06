from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class TraceRecorder:
    user_message: str
    runs_dir: str | Path = "traces/runs"
    run_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    router_result: dict | None = None
    selected_skill: dict | None = None
    case_state: dict | None = None
    retrieved_citations: list[dict] = field(default_factory=list)
    graph_evidence: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    final_answer: str | None = None
    warnings: list[str] = field(default_factory=list)

    def record_router_result(self, router_result: dict) -> None:
        self.router_result = router_result

    def record_selected_skill(self, selected_skill: dict) -> None:
        self.selected_skill = selected_skill

    def record_case_state(self, case_state: dict) -> None:
        self.case_state = case_state

    def record_retrieved_citations(self, citations: list[dict]) -> None:
        self.retrieved_citations = citations

    def record_graph_evidence(self, graph_evidence: list[dict]) -> None:
        self.graph_evidence = graph_evidence

    def record_tool_call(self, tool_name: str, args: dict, result: dict) -> None:
        self.tool_calls.append(
            {
                "tool_name": tool_name,
                "args": args,
                "result": result,
            }
        )

    def record_final_answer(self, final_answer: str) -> None:
        self.final_answer = final_answer

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def to_dict(self) -> dict:
        return asdict(self) | {"runs_dir": str(self.runs_dir)}

    def save(self) -> Path:
        root = Path(self.runs_dir)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{self.run_id}.json"
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

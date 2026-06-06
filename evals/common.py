from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GOLD_CASES_PATH = Path("data/gold_cases.jsonl")


def load_gold_cases(path: str | Path = GOLD_CASES_PATH) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        row["expected_intent"] = row.get("expected_intent", row.get("intent"))
        rows.append(row)
    return rows

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MOCK_DATA_DIR = Path("data/mock")


def load_mock_json(filename: str) -> list[dict[str, Any]]:
    path = MOCK_DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def tool_result(
    *,
    ok: bool,
    action: str,
    data: Any = None,
    error: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "action": action,
        "data": data,
        "error": error,
        "dry_run": dry_run,
    }

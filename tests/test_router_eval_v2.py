from __future__ import annotations

import json

from evals.banking77_router_eval import run_banking77_router_eval


def test_banking77_router_eval_runs_on_sample_fixture(tmp_path):
    output_path = tmp_path / "banking77_router_report.json"
    result = run_banking77_router_eval(
        output_path=output_path,
        max_samples=5,
        sample_path="data/banking77_sample.jsonl",
        allow_fallback=False,
    )

    confusion_path = tmp_path / "banking77_confusion_cases.jsonl"
    assert output_path.exists()
    assert confusion_path.exists()
    assert set(result["methods"]) == {"rule", "tfidf_lr"}

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["dataset"] == "banking77"
    assert "macro_f1" in payload["methods"]["rule"]
    assert "per_class_report" in payload["methods"]["tfidf_lr"]

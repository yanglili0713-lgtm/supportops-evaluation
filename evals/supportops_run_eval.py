from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from evals.supportops_adapters import run_pipeline
from evals.supportops_metrics import aggregate, score_case


DEFAULT_BENCH_PATH = Path("evals/supportops_bench.yaml")
DEFAULT_OUT_PATH = Path("reports/eval_dummy_results.json")
DEFAULT_TRACE_PATH = Path("traces/dummy_traces.jsonl")


def run_eval(
    bench_path: str | Path = DEFAULT_BENCH_PATH,
    pipeline_name: str = "dummy",
    out_path: str | Path = DEFAULT_OUT_PATH,
    trace_out: str | Path = DEFAULT_TRACE_PATH,
) -> dict:
    cases = load_bench(bench_path)
    results = []
    scores = []

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(trace_out).parent.mkdir(parents=True, exist_ok=True)

    with Path(trace_out).open("w", encoding="utf-8") as trace_file:
        for case in cases:
            started = time.perf_counter()
            error = None
            prediction = {"answer": "", "retrieved_docs": [], "route": None, "raw": {}}
            try:
                prediction = run_pipeline(pipeline_name, case["query"])
            except Exception as exc:  # noqa: BLE001 - eval should keep running per case.
                error = str(exc)

            latency_ms = (time.perf_counter() - started) * 1000
            prediction["latency_ms"] = latency_ms
            case_score = score_case(case, prediction)
            scores.append(case_score)

            record = {
                "case_id": case.get("id"),
                "query": case.get("query"),
                "task_type": case.get("task_type"),
                "prediction": {
                    "answer": prediction.get("answer", ""),
                    "retrieved_docs": prediction.get("retrieved_docs", []),
                    "route": prediction.get("route"),
                    "raw": prediction.get("raw", {}),
                },
                "score": case_score,
                "latency_ms": round(latency_ms, 4),
                "error": error,
            }
            results.append(record)
            trace_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = aggregate(scores)
    payload = {
        "pipeline": pipeline_name,
        "bench": str(bench_path),
        "summary": summary,
        "results": results,
    }
    Path(out_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_bench(path: str | Path) -> list[dict[str, Any]]:
    text = Path(path).read_text(encoding="utf-8")
    return _parse_simple_yaml_list(text)


def _parse_simple_yaml_list(text: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list_key: str | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if line.startswith("- ") and indent == 0:
            if current is not None:
                cases.append(current)
            current = {}
            current_list_key = None
            key, value = _split_key_value(line[2:])
            current[key] = _parse_scalar(value)
            continue
        if current is None:
            continue
        if line.startswith("- ") and current_list_key:
            current[current_list_key].append(_parse_scalar(line[2:]))
            continue
        key, value = _split_key_value(line)
        if value == "":
            current[key] = []
            current_list_key = key
        else:
            current[key] = _parse_scalar(value)
            current_list_key = None

    if current is not None:
        cases.append(current)
    return cases


def _split_key_value(line: str) -> tuple[str, str]:
    key, _, value = line.partition(":")
    return key.strip(), value.strip()


def _parse_scalar(value: str) -> Any:
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SupportOpsBench eval.")
    parser.add_argument("--bench", default=str(DEFAULT_BENCH_PATH))
    parser.add_argument("--pipeline", default="dummy")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH))
    parser.add_argument("--trace-out", default=str(DEFAULT_TRACE_PATH))
    args = parser.parse_args()

    payload = run_eval(
        bench_path=args.bench,
        pipeline_name=args.pipeline,
        out_path=args.out,
        trace_out=args.trace_out,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

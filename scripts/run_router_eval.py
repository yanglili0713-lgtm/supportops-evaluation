from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.banking77_router_eval import run_banking77_router_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BANKING77 router evaluation.")
    parser.add_argument("--dataset", default="banking77")
    parser.add_argument("--split", default="test")
    parser.add_argument("--max-samples", type=int, default=1000)
    parser.add_argument("--train-max-samples", type=int, default=None)
    parser.add_argument("--output", default="runs/eval/banking77_router_report.json")
    parser.add_argument("--confusion-out", default=None)
    parser.add_argument("--sample-path", default=None)
    parser.add_argument("--no-fallback", action="store_true")
    args = parser.parse_args()

    if args.dataset != "banking77":
        raise SystemExit("Only --dataset banking77 is supported in this MVP.")

    result = run_banking77_router_eval(
        output_path=args.output,
        confusion_path=args.confusion_out,
        split=args.split,
        max_samples=args.max_samples,
        train_max_samples=args.train_max_samples,
        sample_path=args.sample_path,
        allow_fallback=not args.no_fallback,
    )
    print(json.dumps(result["methods"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

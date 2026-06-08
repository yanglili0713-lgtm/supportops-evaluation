from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.supportops_retrieval_eval import run_supportops_ablation, run_supportops_alpha_sweep


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SupportOps ablation study.")
    parser.add_argument("--dataset", default="supportops")
    parser.add_argument("--output-dir", default="runs/eval")
    parser.add_argument("--bench-path", default="evals/supportops_bench.yaml")
    parser.add_argument("--docs-dir", default="data/docs")
    parser.add_argument(
        "--alpha-sweep",
        default=None,
        help=(
            "Comma-separated alpha values for hybrid fusion. "
            "alpha = 1.0 is more BM25-weighted; alpha = 0.0 is more dense-weighted."
        ),
    )
    return parser


def parse_alpha_sweep(value: str | None) -> list[float]:
    if not value:
        return []
    alphas: list[float] = []
    for raw in value.split(","):
        item = raw.strip()
        if not item:
            continue
        alpha = float(item)
        if alpha < 0 or alpha > 1:
            raise ValueError("alpha values must be between 0 and 1")
        alphas.append(alpha)
    if not alphas:
        raise ValueError("--alpha-sweep did not contain any valid values")
    return alphas


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.dataset != "supportops":
        raise SystemExit("Only --dataset supportops is supported in this MVP.")

    alphas = parse_alpha_sweep(args.alpha_sweep)
    if alphas:
        result = run_supportops_alpha_sweep(
            alphas=alphas,
            output_dir=args.output_dir,
            bench_path=args.bench_path,
            docs_dir=args.docs_dir,
        )
    else:
        result = run_supportops_ablation(
            output_dir=args.output_dir,
            bench_path=args.bench_path,
            docs_dir=args.docs_dir,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

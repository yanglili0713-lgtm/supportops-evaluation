from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.supportops_retrieval_eval import run_supportops_retrieval_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SupportOps retrieval evaluation.")
    parser.add_argument("--dataset", default="supportops")
    parser.add_argument("--methods", default="bm25,hybrid,hybrid_reranker,planner")
    parser.add_argument("--output-dir", default="runs/eval")
    parser.add_argument("--bench-path", default="evals/supportops_bench.yaml")
    parser.add_argument("--docs-dir", default="data/docs")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--chunk-overlap", type=int, default=80)
    parser.add_argument("--search-top-k", type=int, default=30)
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()

    if args.dataset != "supportops":
        raise SystemExit("Only --dataset supportops is supported in this MVP.")

    result = run_supportops_retrieval_eval(
        methods=[method.strip() for method in args.methods.split(",") if method.strip()],
        output_dir=args.output_dir,
        bench_path=args.bench_path,
        docs_dir=args.docs_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        search_top_k=args.search_top_k,
        max_cases=args.max_cases,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

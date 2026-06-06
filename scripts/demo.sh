#!/usr/bin/env bash
set -e

echo "=============================================="
echo "SupportOps Agent Demo"
echo "=============================================="
echo

echo "[1/4] Run all tests"
uv run pytest -q
echo

echo "[2/4] Demo RAG query: 上传PDF后检索不到内容怎么办？"
printf '上传PDF后检索不到内容怎么办？\n' | uv run python -m app.cli
echo

echo "[3/4] Run eval pipeline"
uv run python -m evals.run_all
echo

echo "[4/4] Show generated eval report"
if [ -f "evals/report.md" ]; then
  sed -n '1,200p' evals/report.md
else
  echo "evals/report.md not found"
fi

echo
echo "Demo finished."

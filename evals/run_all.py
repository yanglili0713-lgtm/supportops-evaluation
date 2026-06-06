from __future__ import annotations

import json
from pathlib import Path

from evals import (
    agentic_retry_eval,
    graphrag_eval,
    hybrid_rag_eval,
    memory_regression_eval,
    rag_grounding_eval,
    router_confusion_eval,
    tool_recall_eval,
)


REPORT_PATH = Path("evals/report.md")


def run_all() -> dict:
    results = {
        "tool_recall": tool_recall_eval.run_eval(),
        "router_confusion": router_confusion_eval.run_eval(),
        "memory_regression": memory_regression_eval.run_eval(),
        "rag_grounding": rag_grounding_eval.run_eval(),
        "hybrid_rag": hybrid_rag_eval.run_eval(),
        "graphrag": graphrag_eval.run_eval(),
        "agentic_retry": agentic_retry_eval.run_eval(),
    }
    REPORT_PATH.write_text(_render_report(results), encoding="utf-8")
    return results


def _render_report(results: dict) -> str:
    tool_recall = results["tool_recall"]
    router_confusion = results["router_confusion"]
    memory = results["memory_regression"]
    rag = results["rag_grounding"]
    hybrid = results["hybrid_rag"]
    graphrag = results["graphrag"]
    agentic = results["agentic_retry"]

    return "\n".join(
        [
            "# Eval Report",
            "",
            "## Router accuracy",
            "",
            f"- Accuracy: {tool_recall['accuracy']}",
            f"- Total cases: {tool_recall['total_cases']}",
            f"- Failed cases: {len(tool_recall['failed_cases'])}",
            "",
            "## High confidence wrong routes",
            "",
            _format_json(router_confusion["high_confidence_wrong_route"]),
            "",
            "## Memory regression",
            "",
            f"- Passed: {memory['passed']}",
            f"- Failed checks: {', '.join(memory['failed_checks']) or 'none'}",
            "",
            "## RAG grounding",
            "",
            f"- Passed: {rag['passed']}",
            f"- Failed checks: {', '.join(rag['failed_checks']) or 'none'}",
            "",
            "## Hybrid RAG",
            "",
            f"- Passed: {hybrid['passed']}",
            f"- Failed checks: {', '.join(hybrid['failed_checks']) or 'none'}",
            "",
            "## GraphRAG",
            "",
            f"- Passed: {graphrag['passed']}",
            f"- Failed checks: {', '.join(graphrag['failed_checks']) or 'none'}",
            "",
            "## Agentic retrieval",
            "",
            f"- Passed: {agentic['passed']}",
            f"- Failed checks: {', '.join(agentic['failed_checks']) or 'none'}",
            "",
            "## Current known limitations",
            "",
            "- Evals are small rule checks, not statistically representative benchmarks.",
            "- Router eval depends on keyword gold cases and may miss semantic paraphrases.",
            "- Memory eval covers one synthetic multi-turn case only.",
            "- RAG grounding checks citations and required docs, not answer faithfulness.",
            "- Tool recall is approximated through intent routing until Agent loop tool orchestration exists.",
            "- Hybrid RAG uses an in-memory token vector fallback, not a production embedding model.",
            "- GraphRAG uses in-memory seed data; Neo4j schema is provided as a production design artifact.",
            "- Agentic retrieval is a deterministic local planner, not an LLM policy.",
            "",
        ]
    )


def _format_json(value: object) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


if __name__ == "__main__":
    print(json.dumps(run_all(), ensure_ascii=False, indent=2))

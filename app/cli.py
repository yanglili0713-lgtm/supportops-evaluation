from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rag.pipeline import RAGPipeline


def build_answer(question: str, docs_dir: str = "data/docs") -> dict:
    pipeline = RAGPipeline(docs_dir=docs_dir)
    results = pipeline.query(question, top_k=3)

    citations = [
        {
            "doc_id": r.doc_id,
            "chunk_id": r.chunk_id,
            "source": r.source,
            "score": round(r.score, 4),
        }
        for r in results
    ]

    if not results:
        answer = "没有在知识库中找到足够依据，建议转人工或补充更多信息。"
    else:
        answer = "根据知识库，相关依据如下：\n\n"
        for idx, r in enumerate(results, start=1):
            answer += f"[{idx}] 来源：{r.source}，chunk：{r.chunk_id}\n{r.text[:300]}\n\n"

    trace = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "citations": citations,
        "answer": answer,
    }
    save_trace(trace)

    return trace


def save_trace(trace: dict) -> None:
    root = Path("traces/runs")
    root.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".json"
    (root / filename).write_text(
        json.dumps(trace, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    question = input("请输入用户问题：").strip()
    result = build_answer(question)
    print(result["answer"])
    print("Citations:")
    for citation in result["citations"]:
        print(citation)


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    doc_id: str
    source: str
    text: str


def load_markdown_docs(docs_dir: str | Path = "data/docs") -> list[Document]:
    root = Path(docs_dir)
    if not root.exists():
        raise FileNotFoundError(f"docs_dir not found: {root}")

    docs: list[Document] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                doc_id=path.stem,
                source=str(path),
                text=text,
            )
        )
    return docs

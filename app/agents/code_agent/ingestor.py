"""Ingestion helpers for source code files."""
from __future__ import annotations

# Provide a thin fallback for environments without langchain installed.
try:  # pragma: no cover - prefer the actual loader
    from langchain_community.document_loaders import TextLoader
except Exception:  # pragma: no cover - fallback loader for tests
    from common.text_normalization import Document  # lazy import to avoid cycles

    class TextLoader:  # type: ignore[override]
        def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
            self.file_path = file_path
            self.encoding = encoding

        def load(self):
            with open(self.file_path, "r", encoding=self.encoding) as handle:
                return [Document(page_content=handle.read(), metadata={"source": self.file_path})]

<<<<<<< HEAD:app/agents/code.py
from .base import BaseFileIngestor, IngestionTarget
=======
from ..base import BaseFileIngestor
>>>>>>> master:app/agents/code_agent/ingestor.py

CODE_LOADERS = {
    ".py": (TextLoader, {"encoding": "utf8"}),
    ".js": (TextLoader, {"encoding": "utf8"}),
    ".ts": (TextLoader, {"encoding": "utf8"}),
    ".java": (TextLoader, {"encoding": "utf8"}),
    ".c": (TextLoader, {"encoding": "utf8"}),
    ".cpp": (TextLoader, {"encoding": "utf8"}),
    ".cs": (TextLoader, {"encoding": "utf8"}),
    ".go": (TextLoader, {"encoding": "utf8"}),
    ".rb": (TextLoader, {"encoding": "utf8"}),
    ".rs": (TextLoader, {"encoding": "utf8"}),
    ".php": (TextLoader, {"encoding": "utf8"}),
}

CODE_COLLECTION = "troubleshooting"


CODE_TARGETS = {
    extension: IngestionTarget(
        domain="code",
        collection=CODE_COLLECTION,
        tags=("code", "snippet", extension.lstrip(".")),
    )
    for extension in CODE_LOADERS
}


def create_code_ingestor() -> BaseFileIngestor:
    return BaseFileIngestor(
        domain="code",
        collection_name=CODE_COLLECTION,
        loader_mapping=CODE_LOADERS,
        extension_targets=CODE_TARGETS,
    )


CodeIngestor = create_code_ingestor()

__all__ = [
    "CODE_COLLECTION",
<<<<<<< HEAD:app/agents/code.py
    "CODE_TARGETS",
=======
>>>>>>> master:app/agents/code_agent/ingestor.py
    "CodeIngestor",
    "create_code_ingestor",
]

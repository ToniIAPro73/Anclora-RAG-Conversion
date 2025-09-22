"""Ingestion helpers for multimedia transcripts and captions."""
from __future__ import annotations

try:  # pragma: no cover - use real loader when available
    from langchain_community.document_loaders import TextLoader
except Exception:  # pragma: no cover - fallback loader for tests
    from common.text_normalization import Document

    class TextLoader:  # type: ignore[override]
        def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
            self.file_path = file_path
            self.encoding = encoding

        def load(self):
            with open(self.file_path, "r", encoding=self.encoding) as handle:
                return [Document(page_content=handle.read(), metadata={"source": self.file_path})]

<<<<<<< HEAD:app/agents/multimedia.py
from .base import BaseFileIngestor, IngestionTarget
=======
from ..base import BaseFileIngestor
>>>>>>> master:app/agents/media_agent/ingestor.py

MULTIMEDIA_LOADERS = {
    ".srt": (TextLoader, {"encoding": "utf8"}),
    ".vtt": (TextLoader, {"encoding": "utf8"}),
    ".sbv": (TextLoader, {"encoding": "utf8"}),
    ".ssa": (TextLoader, {"encoding": "utf8"}),
}

MULTIMEDIA_COLLECTION = "multimedia_assets"


MULTIMEDIA_TARGETS = {
    extension: IngestionTarget(
        domain="multimedia",
        collection=MULTIMEDIA_COLLECTION,
        tags=("multimedia", "captions", extension.lstrip(".")),
    )
    for extension in MULTIMEDIA_LOADERS
}


def create_multimedia_ingestor() -> BaseFileIngestor:
    return BaseFileIngestor(
        domain="multimedia",
        collection_name=MULTIMEDIA_COLLECTION,
        loader_mapping=MULTIMEDIA_LOADERS,
        extension_targets=MULTIMEDIA_TARGETS,
    )


MultimediaIngestor = create_multimedia_ingestor()

__all__ = [
    "MULTIMEDIA_COLLECTION",
<<<<<<< HEAD:app/agents/multimedia.py
    "MULTIMEDIA_TARGETS",
=======
>>>>>>> master:app/agents/media_agent/ingestor.py
    "MultimediaIngestor",
    "create_multimedia_ingestor",
]

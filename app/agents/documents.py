"""Document ingestion helpers."""
from __future__ import annotations

from typing import List

# Attempt to import the rich document loaders, providing simple fallbacks for tests.
PLAIN_TEXT_FALLBACK = False

try:  # pragma: no cover - prefer real loaders when available
    from langchain_community.document_loaders import (
        CSVLoader,
        EverNoteLoader,
        PyMuPDFLoader,
        TextLoader,
        UnstructuredEmailLoader,
        UnstructuredEPubLoader,
        UnstructuredHTMLLoader,
        UnstructuredMarkdownLoader,
        UnstructuredODTLoader,
        UnstructuredPowerPointLoader,
        UnstructuredWordDocumentLoader,
    )
except Exception:  # pragma: no cover - fallback path
    PLAIN_TEXT_FALLBACK = True
    class _PlainTextLoader:
        def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
            self.file_path = file_path
            self.encoding = encoding

        def load(self) -> List[Document]:
            with open(self.file_path, "r", encoding=self.encoding) as handle:
                content = handle.read()
            return [Document(page_content=content, metadata={"source": self.file_path})]

    CSVLoader = EverNoteLoader = PyMuPDFLoader = UnstructuredEmailLoader = _PlainTextLoader
    UnstructuredEPubLoader = UnstructuredHTMLLoader = UnstructuredMarkdownLoader = _PlainTextLoader
    UnstructuredODTLoader = UnstructuredPowerPointLoader = UnstructuredWordDocumentLoader = _PlainTextLoader
    TextLoader = _PlainTextLoader

from common.text_normalization import Document

from .base import BaseFileIngestor


if not PLAIN_TEXT_FALLBACK:
    class EmailFallbackLoader(UnstructuredEmailLoader):
        """Wrapper providing a graceful fallback for plain text emails."""

        def load(self) -> List[Document]:  # type: ignore[override]
            try:
                try:
                    return super().load()
                except ValueError as exc:
                    if "text/html content not found in email" not in str(exc):
                        raise
                    self.unstructured_kwargs["content_source"] = "text/plain"
                    return super().load()
            except Exception as exc:  # pragma: no cover - error enrichment
                raise type(exc)(f"{self.file_path}: {exc}") from exc
else:  # pragma: no cover - simplified behavior for tests
    EmailFallbackLoader = UnstructuredEmailLoader  # type: ignore


DOCUMENT_LOADERS = {
    ".csv": (CSVLoader, {}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".enex": (EverNoteLoader, {}),
    ".eml": (EmailFallbackLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PyMuPDFLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
}


DOCUMENTS_COLLECTION = "conversion_rules"


def create_document_ingestor() -> BaseFileIngestor:
    """Factory for the document ingestor."""

    return BaseFileIngestor(
        domain="documents",
        collection_name=DOCUMENTS_COLLECTION,
        loader_mapping=DOCUMENT_LOADERS,
    )


DocumentIngestor = create_document_ingestor()

__all__ = ["DocumentIngestor", "create_document_ingestor", "DOCUMENTS_COLLECTION"]

"""Document ingestion helpers."""
from __future__ import annotations

import sys
from typing import Dict, List, Tuple

from common.text_normalization import Document

from ..base import BaseFileIngestor


PLAIN_TEXT_FALLBACK = False
_LOADER_MODULE = "langchain_community.document_loaders"
_CURRENT_LOADER_MODULE_ID: int | None = None


def _build_loader_mapping() -> Tuple[Dict[str, Tuple[type, Dict[str, object]]], type]:
    """Instantiate the loader mapping, falling back to plain text readers if needed."""

    global PLAIN_TEXT_FALLBACK

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
    except Exception:  # pragma: no cover - fallback path used in tests without langchain
        PLAIN_TEXT_FALLBACK = True

        class _FallbackDocument:
            __slots__ = ("page_content", "metadata")

            def __init__(self, page_content: str, metadata: Dict[str, object]) -> None:
                self.page_content = page_content
                self.metadata = metadata

        class _PlainTextLoader:
            def __init__(self, file_path: str, encoding: str = "utf8", **_: object) -> None:
                self.file_path = file_path
                self.encoding = encoding

            def load(self) -> List[Document]:
                with open(self.file_path, "r", encoding=self.encoding) as handle:
                    content = handle.read()
                metadata = {"source": self.file_path}
                try:
                    return [Document(page_content=content, metadata=metadata)]
                except TypeError:
                    return [_FallbackDocument(page_content=content, metadata=metadata)]

        EmailLoader = _PlainTextLoader

        loader_map: Dict[str, Tuple[type, Dict[str, object]]] = {
            ".csv": (_PlainTextLoader, {}),
            ".doc": (_PlainTextLoader, {}),
            ".docx": (_PlainTextLoader, {}),
            ".enex": (_PlainTextLoader, {}),
            ".eml": (_PlainTextLoader, {}),
            ".epub": (_PlainTextLoader, {}),
            ".html": (_PlainTextLoader, {}),
            ".md": (_PlainTextLoader, {}),
            ".odt": (_PlainTextLoader, {}),
            ".pdf": (_PlainTextLoader, {}),
            ".ppt": (_PlainTextLoader, {}),
            ".pptx": (_PlainTextLoader, {}),
            ".txt": (_PlainTextLoader, {"encoding": "utf8"}),
        }
        return loader_map, EmailLoader

    PLAIN_TEXT_FALLBACK = False

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

    loader_map = {
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
    return loader_map, EmailFallbackLoader


def _current_loader_module_id() -> int | None:
    module = sys.modules.get(_LOADER_MODULE)
    return id(module) if module is not None else None


DOCUMENT_LOADERS, EmailFallbackLoader = _build_loader_mapping()
_CURRENT_LOADER_MODULE_ID = _current_loader_module_id()


def refresh_document_loaders(force: bool = False) -> None:
    """Reload loader implementations when new backends become available."""

    global DOCUMENT_LOADERS, EmailFallbackLoader, _CURRENT_LOADER_MODULE_ID

    loader_module_id = _current_loader_module_id()
    if (
        not force
        and not PLAIN_TEXT_FALLBACK
        and loader_module_id is not None
        and loader_module_id == _CURRENT_LOADER_MODULE_ID
    ):
        return

    loader_map, email_loader = _build_loader_mapping()
    DOCUMENT_LOADERS = loader_map
    EmailFallbackLoader = email_loader
    _CURRENT_LOADER_MODULE_ID = loader_module_id if not PLAIN_TEXT_FALLBACK else None

    ingestor = globals().get("DocumentIngestor")
    if isinstance(ingestor, BaseFileIngestor):
        ingestor.loader_mapping = DOCUMENT_LOADERS


DOCUMENTS_COLLECTION = "conversion_rules"


def create_document_ingestor() -> BaseFileIngestor:
    """Factory for the document ingestor."""

    refresh_document_loaders()

    return BaseFileIngestor(
        domain="documents",
        collection_name=DOCUMENTS_COLLECTION,
        loader_mapping=DOCUMENT_LOADERS,
    )


DocumentIngestor = create_document_ingestor()

__all__ = [
    "DOCUMENTS_COLLECTION",
    "DocumentIngestor",
    "EmailFallbackLoader",
    "create_document_ingestor",
    "refresh_document_loaders",
]

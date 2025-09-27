"""Utility helpers for consistent text normalization across ingestion and querying."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

try:  # pragma: no cover - the import path is environment dependent
    from langchain_core.documents import Document as _LangChainDocument  # type: ignore[assignment]
except Exception:  # pragma: no cover - fallback for stripped environments
    @dataclass
    class _LangChainDocument:  # type: ignore[override]
        """Minimal stand-in for ``langchain``'s :class:`Document`.

        It captures the fields used throughout the project so tests can run in
        environments where the upstream dependency is unavailable.
        """

        def __init__(self, page_content: str, **kwargs):
            self.page_content = page_content
            self.metadata = kwargs


Document = _LangChainDocument

class _SimpleDocument:
    __slots__ = ("page_content", "metadata")

    def __init__(self, page_content: str, metadata: Dict[str, Any]) -> None:
        self.page_content = page_content
        self.metadata = metadata


NORMALIZATION_FORM = "NFC"


def normalize_to_nfc(text: str) -> str:
    """Return the NFC-normalized version of *text*.

    Empty strings are returned untouched and ``None`` inputs yield an empty
    string, allowing callers to work with optional values without additional
    guards.
    """
    if text is None:
        return ""
    return unicodedata.normalize(NORMALIZATION_FORM, text)


def normalize_documents_nfc(documents: Iterable[Document]) -> List[Document]:
    """Normalize page content of ``documents`` using NFC.

    The original page content is preserved in the ``original_page_content``
    metadata field to retain the exact bytes that were ingested.
    """
    normalized_docs: List[Document] = []
    for doc in documents:
        original_content = doc.page_content or ""
        normalized_content = normalize_to_nfc(original_content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata["original_page_content"] = original_content
        metadata["normalization"] = NORMALIZATION_FORM
        try:
            normalized_docs.append(
                Document(page_content=normalized_content, metadata=metadata)
            )
        except TypeError:
            normalized_docs.append(_SimpleDocument(page_content=normalized_content, metadata=metadata))
    return normalized_docs


__all__ = [
    "Document",
    "normalize_documents_nfc",
    "normalize_to_nfc",
    "NORMALIZATION_FORM",
]

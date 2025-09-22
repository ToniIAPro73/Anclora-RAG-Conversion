"""Tests for ensuring files are routed to the proper Chroma collection."""
from __future__ import annotations

import io
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterable, List

import pytest

from app.common import ingest_file as ingest_module


@dataclass
class _RecordedCall:
    collection: str
    documents: List[object]


class _DummyStreamlit:
    def __init__(self) -> None:
        self.messages: List[tuple[str, tuple, Dict]] = []

    def warning(self, *args, **kwargs):
        self.messages.append(("warning", args, kwargs))

    def success(self, *args, **kwargs):
        self.messages.append(("success", args, kwargs))

    def info(self, *args, **kwargs):
        self.messages.append(("info", args, kwargs))

    def error(self, *args, **kwargs):
        self.messages.append(("error", args, kwargs))

    @contextmanager
    def spinner(self, *_args, **_kwargs):
        yield


class _FakeCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self._records: List[dict] = []

    def add_records(self, documents: Iterable[object]) -> None:
        for document in documents:
            record_id = f"{self.name}_{len(self._records)}"
            self._records.append(
                {
                    "id": record_id,
                    "metadata": dict(document.metadata),
                    "document": document.page_content,
                }
            )

    def count(self) -> int:
        return len(self._records)

    def get(self, include=None, where=None):  # noqa: D401 - match chroma signature
        records = list(self._records)
        if where:
            records = [
                record
                for record in records
                if all(record["metadata"].get(key) == value for key, value in where.items())
            ]
        return {
            "ids": [record["id"] for record in records],
            "metadatas": [dict(record["metadata"]) for record in records],
            "documents": [record["document"] for record in records],
        }

    def delete(self, ids=None):
        if ids is None:
            self._records.clear()
            return
        ids_set = set(ids)
        self._records = [record for record in self._records if record["id"] not in ids_set]


class _FakeChromaClient:
    def __init__(self) -> None:
        self._collections: Dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        return self._collections.setdefault(name, _FakeCollection(name))


def _install_chroma_stub(monkeypatch: pytest.MonkeyPatch):
    records: List[_RecordedCall] = []
    fake_client = _FakeChromaClient()

    class _RecordingChroma:
        def __init__(self, collection_name: str, embedding_function=None, client=None, **_):
            self.collection_name = collection_name
            self._client = client or fake_client
            self._collection = self._client.get_or_create_collection(collection_name)

        def add_documents(self, documents):
            records.append(_RecordedCall(self.collection_name, list(documents)))
            self._collection.add_records(documents)

        @classmethod
        def from_documents(cls, documents, embedding=None, client=None, collection_name=None, **_):
            instance = cls(collection_name=collection_name, embedding_function=embedding, client=client)
            instance.add_documents(documents)
            return instance

    monkeypatch.setattr(ingest_module, "Chroma", _RecordingChroma, raising=False)
    monkeypatch.setattr(ingest_module, "CHROMA_SETTINGS", fake_client, raising=False)
    streamlit_stub = _DummyStreamlit()
    monkeypatch.setattr(ingest_module, "st", streamlit_stub, raising=False)

    return records, streamlit_stub


class _UploadedFile(io.BytesIO):
    def __init__(self, name: str, content: str) -> None:
        super().__init__(content.encode("utf-8"))
        self.name = name
        self.size = len(content.encode("utf-8"))


@pytest.mark.parametrize(
    "filename, expected_domain, expected_collection",
    [
        ("manual.txt", "documents", "conversion_rules"),
        ("script.py", "code", "troubleshooting"),
        ("captions.srt", "multimedia", "multimedia_assets"),
    ],
)
def test_files_are_routed_to_expected_collection(monkeypatch, filename, expected_domain, expected_collection):
    records, streamlit_stub = _install_chroma_stub(monkeypatch)

    uploaded = _UploadedFile(filename, "Contenido de prueba")
    ingest_module.ingest_file(uploaded, filename)

    assert records, f"No se registraron ingestas: {streamlit_stub.messages}"
    last_call = records[-1]
    assert last_call.collection == expected_collection
    for document in last_call.documents:
        assert document.metadata["collection"] == expected_collection
        assert document.metadata["domain"] == expected_domain
        assert document.metadata["uploaded_file_name"] == filename


@pytest.mark.parametrize(
    "domain, expected_collection",
    [
        ("documents", "conversion_rules"),
        ("code", "troubleshooting"),
        ("multimedia", "multimedia_assets"),
        ("formats", "format_specs"),
        ("guides", "knowledge_guides"),
        ("compliance", "compliance_archive"),
    ],
)
def test_domain_to_collection_contains_expected_mappings(domain, expected_collection):
    from app.common.constants import CHROMA_COLLECTIONS, DOMAIN_TO_COLLECTION

    assert DOMAIN_TO_COLLECTION[domain] == expected_collection
    assert CHROMA_COLLECTIONS[expected_collection].domain == domain

"""API upload routing tests."""
from __future__ import annotations

import io
import sys
import types
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import pytest
from fastapi.testclient import TestClient

from app import api_endpoints

AUTH_HEADERS = {"Authorization": "Bearer your-api-key-here"}


@dataclass
class _RecordedCall:
    collection: str
    documents: List[object]


class _DummyStreamlit:
    def __init__(self) -> None:
        self.messages: List[Tuple[str, Tuple, Dict]] = []

    def warning(self, *args, **kwargs):
        self.messages.append(("warning", args, kwargs))

    def success(self, *args, **kwargs):
        self.messages.append(("success", args, kwargs))

    def info(self, *args, **kwargs):
        self.messages.append(("info", args, kwargs))

    def error(self, *args, **kwargs):
        self.messages.append(("error", args, kwargs))

    def spinner(self, *_args, **_kwargs):  # pragma: no cover - compatibility
        @dataclass
        class _DummySpinner:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *_exc):
                return False

        return _DummySpinner()


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


class _FakeChromaClient:
    def __init__(self) -> None:
        self._collections: Dict[str, _FakeCollection] = {}

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        return self._collections.setdefault(name, _FakeCollection(name))


@pytest.fixture
def upload_env(monkeypatch: pytest.MonkeyPatch):
    from app.common import ingest_file as ingest_module

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

    streamlit_stub = _DummyStreamlit()

    monkeypatch.setattr(ingest_module, "Chroma", _RecordingChroma, raising=False)
    monkeypatch.setattr(ingest_module, "CHROMA_SETTINGS", fake_client, raising=False)
    monkeypatch.setattr(ingest_module, "st", streamlit_stub, raising=False)
    monkeypatch.setattr(ingest_module, "get_embeddings", lambda: object(), raising=False)
    common_pkg = sys.modules.setdefault("common", types.ModuleType("common"))
    monkeypatch.setattr(common_pkg, "ingest_file", ingest_module, raising=False)
    monkeypatch.setitem(sys.modules, "common.ingest_file", ingest_module)

    client = TestClient(api_endpoints.app)
    return records, streamlit_stub, client


@pytest.mark.parametrize(
    "filename, expected_domain, expected_collection",
    [
        ("manual.txt", "best_practices", "best_practices"),
        ("specification.pdf", "format_specifications", "format_specifications"),
        ("compliance.eml", "legal_compliance", "legal_compliance"),
    ],
)
def test_upload_endpoint_routes_files_correctly(upload_env, filename, expected_domain, expected_collection):
    records, _streamlit_stub, client = upload_env

    file_data = {"file": (filename, io.BytesIO(b"contenido de prueba"), "application/octet-stream")}
    response = client.post("/upload", files=file_data, headers=AUTH_HEADERS)

    assert response.status_code == 200, response.json()
    assert records, "La ingesta no generó registros en Chroma"
    last_call = records[-1]
    assert last_call.collection == expected_collection
    for document in last_call.documents:
        metadata = document.metadata
        assert metadata["collection"] == expected_collection
        assert metadata["domain"] == expected_domain
        assert metadata["uploaded_file_name"] == filename
        assert metadata["source_extension"] == filename.rsplit(".", 1)[-1]
        tags = metadata.get("tags", [])
        assert expected_domain in tags
        assert expected_collection in tags
        assert filename.rsplit(".", 1)[-1] in tags

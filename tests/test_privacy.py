"""Tests for the privacy utilities in ``app.common.privacy``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping

from app.common.privacy import (
    ANONYMIZED_VALUE,
    PrivacyAuditLogger,
    PrivacyManager,
)


class _StubCollection:
    def __init__(self, documents: Mapping[str, Dict[str, object]]) -> None:
        self._documents = dict(documents)
        self.deleted_ids: list[list[str]] = []

    def get(self, where: Mapping[str, object] | None = None, include: list[str] | None = None):
        ids: list[str] = []
        metadatas: list[Dict[str, object]] = []
        for doc_id, metadata in self._documents.items():
            if self._matches(metadata, where):
                ids.append(doc_id)
                metadatas.append(dict(metadata))
        return {"ids": ids, "metadatas": metadatas}

    def delete(self, ids: list[str] | None = None) -> None:
        if not ids:
            return
        self.deleted_ids.append(list(ids))
        for doc_id in ids:
            self._documents.pop(doc_id, None)

    @staticmethod
    def _matches(metadata: Mapping[str, object], where: Mapping[str, object] | None) -> bool:
        if not where:
            return True
        for key, value in where.items():
            candidate = metadata.get(key)
            if key == "source" and isinstance(candidate, str) and isinstance(value, str):
                if candidate.endswith(value):
                    continue
            if candidate != value:
                return False
        return True


class _StubChromaClient:
    def __init__(self, collections: Mapping[str, _StubCollection]) -> None:
        self._collections = collections

    def get_or_create_collection(self, name: str) -> _StubCollection:
        return self._collections[name]


def test_privacy_manager_deletes_collections_and_storage(tmp_path: Path) -> None:
    """The manager should remove vector entries and temporary files."""

    storage_dir = tmp_path / "documents"
    storage_dir.mkdir()
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()

    filename = "datos_cliente.pdf"
    (storage_dir / filename).write_text("contenido")
    (temp_dir / f"123_{filename}").write_text("temporal")

    collection = _StubCollection(
        {
            "id-1": {"uploaded_file_name": filename},
            "id-2": {"uploaded_file_name": "otro.pdf"},
        }
    )
    collections = {"conversion_rules": collection}
    chroma = _StubChromaClient(collections)

    audit_log = tmp_path / "audit.log"

    manager = PrivacyManager(
        chroma_client=chroma,
        collections=collections,
        storage_locations=[storage_dir],
        temporary_locations=[temp_dir],
        audit_logger=PrivacyAuditLogger(log_path=audit_log),
    )

    summary = manager.forget_document(
        filename,
        requested_by="tester",
        subject_id="user-42",
        reason="GDPR",
        extra_metadata={"email": "person@example.com", "notes": "Eliminar"},
    )

    assert summary.status == "deleted"
    assert "conversion_rules" in summary.removed_collections
    assert {path.name for path in summary.removed_files} == {filename, f"123_{filename}"}
    assert not (storage_dir / filename).exists()
    assert not any(temp_dir.iterdir())
    assert collection.deleted_ids and collection.deleted_ids[-1] == ["id-1"]
    assert summary.metadata["email"] == ANONYMIZED_VALUE

    log_payload = json.loads(audit_log.read_text(encoding="utf-8").splitlines()[-1])
    assert log_payload["audit_id"] == summary.audit_id
    assert log_payload["metadata"]["email"] == ANONYMIZED_VALUE
    assert "person@example.com" not in audit_log.read_text(encoding="utf-8")


def test_privacy_manager_reports_missing_documents(tmp_path: Path) -> None:
    """The manager should return ``not_found`` when nothing matches."""

    collections = {"conversion_rules": _StubCollection({})}
    chroma = _StubChromaClient(collections)
    manager = PrivacyManager(
        chroma_client=chroma,
        collections=collections,
        storage_locations=[tmp_path / "docs"],
        temporary_locations=[tmp_path / "tmp"],
        audit_logger=PrivacyAuditLogger(log_path=tmp_path / "audit.log"),
    )

    summary = manager.forget_document("no_existe.txt", requested_by="tester")

    assert summary.status == "not_found"
    assert not summary.removed_collections
    assert not summary.removed_files

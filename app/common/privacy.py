"""Utilities to enforce privacy requests and anonymize stored metadata."""
from __future__ import annotations

import json
import logging
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .constants import CHROMA_COLLECTIONS, CHROMA_SETTINGS

logger = logging.getLogger(__name__)


ANONYMIZED_VALUE = "***REDACTED***"
_SENSITIVE_KEYWORDS = (
    "name",
    "email",
    "phone",
    "user",
    "customer",
    "document",
    "identifier",
    "dni",
    "ssn",
)


@dataclass(slots=True)
class PrivacyAuditRecord:
    """Structured payload describing a privacy related action."""

    audit_id: str
    filename: str
    requested_by: str
    status: str
    message: str
    collections: Sequence[str]
    removed_files: Sequence[Path]
    subject_id: str | None = None
    reason: str | None = None
    metadata: Mapping[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class PrivacyActionSummary:
    """Result of executing the right-to-be-forgotten workflow."""

    filename: str
    status: str
    message: str
    audit_id: str
    removed_collections: Sequence[str]
    removed_files: Sequence[Path]
    metadata: Mapping[str, Any]


class PrivacyAuditLogger:
    """Persistent logger that stores structured privacy audit records."""

    def __init__(self, log_path: str | Path | None = None) -> None:
        self.log_path = Path(log_path) if log_path is not None else Path("logs") / "privacy_audit.log"
        logger_name = f"privacy_audit.{self.log_path.resolve()}"
        self._logger = logging.getLogger(logger_name)
        if not self._logger.handlers:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(self.log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

    def log(self, record: PrivacyAuditRecord) -> None:
        payload = {
            "audit_id": record.audit_id,
            "timestamp": record.timestamp.isoformat(),
            "filename": record.filename,
            "requested_by": record.requested_by,
            "status": record.status,
            "message": record.message,
            "subject_id": record.subject_id,
            "reason": record.reason,
            "collections": list(record.collections),
            "removed_files": [str(path) for path in record.removed_files],
            "metadata": record.metadata or {},
        }
        self._logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))


class PrivacyManager:
    """Centralizes privacy preserving utilities for the RAG platform."""

    def __init__(
        self,
        *,
        chroma_client: Any | None = None,
        collections: Mapping[str, Any] | None = None,
        storage_locations: Sequence[str | Path] | None = None,
        temporary_locations: Sequence[str | Path] | None = None,
        audit_logger: PrivacyAuditLogger | None = None,
    ) -> None:
        self._chroma_client = chroma_client or CHROMA_SETTINGS
        self._collections = collections or CHROMA_COLLECTIONS
        storage_roots = [Path(location) for location in (storage_locations or (Path("documents"),))]
        temp_roots = [Path(location) for location in (temporary_locations or (Path(tempfile.gettempdir()), Path("documents")))]
        self._storage_locations = tuple(storage_roots)
        self._temporary_locations = tuple(temp_roots)
        self._audit_logger = audit_logger or PrivacyAuditLogger()

    # ---------------------------------------------------------------------
    # Metadata handling helpers
    def anonymize_metadata(self, metadata: Mapping[str, Any]) -> dict[str, Any]:
        """Return a sanitized copy of ``metadata`` with sensitive values redacted."""

        def _sanitize(key: str, value: Any) -> Any:
            if isinstance(value, Mapping):
                return {inner_key: _sanitize(inner_key, inner_value) for inner_key, inner_value in value.items()}
            if isinstance(value, list):
                return [_sanitize(key, item) for item in value]
            if isinstance(value, str) and self._is_sensitive_field(key, value):
                return self._mask_value(value)
            return value

        return {key: _sanitize(key, value) for key, value in metadata.items()}

    def _is_sensitive_field(self, key: str, value: str) -> bool:
        lowered = key.lower()
        if any(keyword in lowered for keyword in _SENSITIVE_KEYWORDS):
            return True
        if "@" in value:
            return True
        if value.strip().isdigit() and len(value.strip()) >= 6:
            return True
        return False

    @staticmethod
    def _mask_value(value: str) -> str:
        return ANONYMIZED_VALUE

    # ------------------------------------------------------------------
    # Deletion helpers
    def forget_document(
        self,
        filename: str,
        *,
        requested_by: str,
        subject_id: str | None = None,
        reason: str | None = None,
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> PrivacyActionSummary:
        """Remove document traces from vector stores and temporary storage."""

        if not filename or not filename.strip():
            raise ValueError("filename must be a non-empty string")

        filename = filename.strip()
        audit_id = uuid.uuid4().hex

        deleted_collections = self._delete_from_collections(filename)
        removed_files = self._remove_local_artifacts(filename)

        status = "deleted" if deleted_collections or removed_files else "not_found"
        message = (
            "Documento eliminado de la base de conocimiento y del almacenamiento temporal / "
            "Document removed from the knowledge base and temporary storage"
            if status == "deleted"
            else "No se encontraron coincidencias para el documento solicitado / "
            "No entries matching the document were found"
        )

        metadata = self.anonymize_metadata(extra_metadata or {})

        record = PrivacyAuditRecord(
            audit_id=audit_id,
            filename=filename,
            requested_by=requested_by,
            status=status,
            message=message,
            subject_id=subject_id,
            reason=reason,
            collections=deleted_collections,
            removed_files=removed_files,
            metadata=metadata,
        )

        try:
            self._audit_logger.log(record)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("No fue posible registrar la auditoría de privacidad: %s", exc)

        return PrivacyActionSummary(
            filename=filename,
            status=status,
            message=message,
            audit_id=audit_id,
            removed_collections=deleted_collections,
            removed_files=removed_files,
            metadata=metadata,
        )

    # Internal helpers -------------------------------------------------
    def _delete_from_collections(self, filename: str) -> list[str]:
        affected: list[str] = []
        for collection_name in self._collections:
            try:
                collection = self._chroma_client.get_or_create_collection(collection_name)
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.error("No se pudo obtener la colección %s: %s", collection_name, exc)
                continue

            ids_to_delete = self._find_matching_ids(collection, filename)
            if not ids_to_delete:
                continue

            try:
                collection.delete(ids=list(ids_to_delete))
            except Exception as exc:  # pragma: no cover - delete may fail
                logger.error("No se pudo eliminar %s de la colección %s: %s", filename, collection_name, exc)
                continue

            affected.append(collection_name)

        return affected

    def _find_matching_ids(self, collection: Any, filename: str) -> list[str]:
        """Return ids within *collection* that reference *filename*."""

        queries = (
            {"uploaded_file_name": filename},
            {"source": filename},
        )
        for query in queries:
            try:
                response = collection.get(where=query, include=["ids", "metadatas"])
            except Exception:
                continue
            ids = self._extract_matching_ids(response, filename)
            if ids:
                return ids

        try:
            response = collection.get(include=["ids", "metadatas"])
        except Exception:  # pragma: no cover - compatibility fallback
            return []
        return self._extract_matching_ids(response, filename)

    @staticmethod
    def _extract_matching_ids(response: Any, filename: str) -> list[str]:
        if not isinstance(response, Mapping):
            return []

        raw_ids = response.get("ids") or []
        metadatas = response.get("metadatas") or []

        matched: list[str] = []
        for doc_id, metadata in zip(raw_ids, metadatas):
            if not isinstance(doc_id, str) or not isinstance(metadata, Mapping):
                continue
            uploaded_name = metadata.get("uploaded_file_name")
            source = metadata.get("source")
            if uploaded_name == filename:
                matched.append(doc_id)
                continue
            if isinstance(source, str) and source.endswith(filename):
                matched.append(doc_id)

        return matched

    def _remove_local_artifacts(self, filename: str) -> list[Path]:
        removed: list[Path] = []
        for location in self._storage_locations:
            removed.extend(self._unlink_matches(location, filename, recursive=True))
        for location in self._temporary_locations:
            removed.extend(self._unlink_matches(location, filename, recursive=False, allow_suffix=True))

        # Remove duplicates while preserving order
        seen: set[Path] = set()
        unique_removed: list[Path] = []
        for path in removed:
            if path in seen:
                continue
            seen.add(path)
            unique_removed.append(path)
        return unique_removed

    def _unlink_matches(
        self,
        base_path: Path,
        filename: str,
        *,
        recursive: bool,
        allow_suffix: bool = False,
    ) -> list[Path]:
        if not base_path.exists() or not base_path.is_dir():
            return []

        patterns: Iterable[str]
        if allow_suffix:
            patterns = (filename, f"*{filename}")
        else:
            patterns = (filename,)

        matches: list[Path] = []
        iterator = base_path.rglob if recursive else base_path.glob
        for pattern in patterns:
            try:
                for candidate in iterator(pattern):
                    if not candidate.is_file():
                        continue
                    try:
                        candidate.unlink()
                        matches.append(candidate)
                    except FileNotFoundError:
                        continue
            except Exception:  # pragma: no cover - e.g. permission issues
                continue
        return matches


__all__ = [
    "ANONYMIZED_VALUE",
    "PrivacyActionSummary",
    "PrivacyAuditLogger",
    "PrivacyManager",
]


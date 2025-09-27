"""Validation helpers for the advanced ingestion system."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

from common.logger import Logger


class ValidationService:
    """Validate uploaded artefacts before they are handed to the pipeline."""

    def __init__(self) -> None:
        self._logger = Logger(__name__)

    async def validate_file(
        self,
        file_obj: Any,
        max_file_size: int,
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, Any]:
        """Validate an in-memory uploaded file-like object."""

        return await asyncio.to_thread(
            self._validate_file_sync,
            file_obj,
            max_file_size,
            supported_formats,
        )

    async def validate_file_path(
        self,
        file_path: str,
        max_file_size: int,
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, Any]:
        """Validate a file referenced by an absolute path."""

        return await asyncio.to_thread(
            self._validate_file_path_sync,
            file_path,
            max_file_size,
            supported_formats,
        )

    # ------------------------------------------------------------------
    def _validate_file_sync(
        self,
        file_obj: Any,
        max_file_size: int,
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, Any]:
        name = getattr(file_obj, "name", "untitled")
        extension = self._normalise_extension(name)
        category = self._detect_category(extension, supported_formats)
        size, error = self._safe_size(file_obj)

        if error:
            return {
                "valid": False,
                "error": error,
                "warnings": [],
                "size": size,
                "extension": extension,
                "category": category,
            }

        validation = self._evaluate(size, extension, max_file_size, category, supported_formats)
        validation["size"] = size
        validation["extension"] = extension
        validation["category"] = category
        return validation

    def _validate_file_path_sync(
        self,
        file_path: str,
        max_file_size: int,
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"valid": False, "error": f"File not found: {file_path}", "warnings": [], "size": 0, "extension": None, "category": None}
        if not path.is_file():
            return {"valid": False, "error": f"Path is not a file: {file_path}", "warnings": [], "size": 0, "extension": None, "category": None}

        try:
            size = path.stat().st_size
        except OSError as exc:  # pragma: no cover - defensive guard
            self._logger.error("Unable to read file size for %s: %s", file_path, exc)
            return {"valid": False, "error": f"Could not read file size: {exc}", "warnings": [], "size": 0, "extension": None, "category": None}

        extension = self._normalise_extension(path.name)
        category = self._detect_category(extension, supported_formats)
        validation = self._evaluate(size, extension, max_file_size, category, supported_formats)
        validation["size"] = size
        validation["extension"] = extension
        validation["category"] = category
        return validation

    # ------------------------------------------------------------------
    def _evaluate(
        self,
        size: int,
        extension: Optional[str],
        max_file_size: int,
        category: Optional[str],
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, Any]:
        warnings: list[str] = []
        error: Optional[str] = None

        if size <= 0:
            error = "archivo vacio o sin datos detectables"
        elif size > max_file_size:
            error = f"archivo demasiado grande (maximo {max_file_size // (1024 * 1024)}MB)"
        elif size > max_file_size * 0.9:
            warnings.append("El archivo se acerca al tamano maximo soportado")

        if extension is None:
            error = error or "No se pudo determinar la extension del archivo"
        elif category is None:
            error = error or f"Tipo de archivo no soportado: {extension}"

        return {
            "valid": error is None,
            "error": error,
            "warnings": warnings,
        }

    def _normalise_extension(self, name: str) -> Optional[str]:
        _, ext = os.path.splitext(name)
        return ext.lower() if ext else None

    def _detect_category(self, extension: Optional[str], supported_formats: Dict[str, Iterable[str]]) -> Optional[str]:
        if not extension:
            return None
        for category, extensions in supported_formats.items():
            if extension in set(extensions):
                return category
        return None

    def _safe_size(self, file_obj: Any) -> Tuple[int, Optional[str]]:
        if hasattr(file_obj, "size"):
            try:
                return int(file_obj.size), None
            except Exception as exc:  # pragma: no cover - defensive path
                self._logger.warning("Unexpected size attribute for %s: %s", getattr(file_obj, "name", "unknown"), exc)

        if hasattr(file_obj, "tell") and hasattr(file_obj, "seek"):
            try:
                current = file_obj.tell()
                file_obj.seek(0, os.SEEK_END)
                size = file_obj.tell()
                file_obj.seek(current)
                return int(size), None
            except Exception as exc:  # pragma: no cover - defensive path
                self._logger.error("Failed to determine file size: %s", exc)
                return 0, str(exc)

        try:
            data = file_obj.read()
            size = len(data)
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            return size, None
        except Exception as exc:  # pragma: no cover - defensive path
            self._logger.error("Could not read file to determine size: %s", exc)
            return 0, str(exc)


__all__ = ["ValidationService"]

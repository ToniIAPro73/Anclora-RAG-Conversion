"""Utilities for handling file ingestion tasks."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Any, Dict, Optional

from app.common.logger import Logger
from app.common import ingest_file as ingest_module


class FileProcessor:
    """Bridge between the advanced ingestion system and legacy ingestion helpers."""

    def __init__(self) -> None:
        self._logger = Logger(__name__)

    async def process_uploaded_file(
        self,
        file_obj: Any,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a Streamlit uploaded file asynchronously."""

        return await asyncio.to_thread(self._process_sync, file_obj, extra_metadata or {})

    async def process_file_path(
        self,
        file_path: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Open and ingest a file located on disk."""

        return await asyncio.to_thread(self._process_path_sync, file_path, extra_metadata or {})

    # ------------------------------------------------------------------
    def _process_path_sync(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        with path.open("rb") as handle:
            buffer = io.BytesIO(handle.read())

        buffer.name = path.name  # type: ignore[attr-defined]
        buffer.seek(0)
        metadata.setdefault("source_path", str(path.resolve()))
        metadata.setdefault("inferred_category", metadata.get("category"))
        return self._process_sync(buffer, metadata)

    def _process_sync(self, file_obj: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
        file_name = getattr(file_obj, "name", "unnamed_file")
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            result = ingest_module.ingest_file(file_obj, file_name)
        finally:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)

        success = bool(result.get("success")) if isinstance(result, dict) else False
        error = result.get("error") if isinstance(result, dict) else None
        payload = {
            "file_name": file_name,
            "success": success,
            "result": result,
            "error": error,
            "metadata": metadata,
        }
        if success:
            self._logger.info("Archivo ingerido correctamente: %s", file_name)
        else:
            self._logger.warning("Ingesta con errores para %s: %s", file_name, error)
        return payload


__all__ = ["FileProcessor"]

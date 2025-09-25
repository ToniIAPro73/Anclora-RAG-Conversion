from __future__ import annotations

import io
import asyncio

from app.ingestion.config import DEFAULT_MAX_FILE_SIZE, DEFAULT_SUPPORTED_FORMATS
from app.ingestion.validation_service import ValidationService


def test_validation_service_accepts_supported_document() -> None:
    service = ValidationService()
    file_obj = io.BytesIO(b"hello world")
    file_obj.name = "sample.txt"  # type: ignore[attr-defined]
    file_obj.size = len(file_obj.getvalue())  # type: ignore[attr-defined]

    result = asyncio.run(service.validate_file(file_obj, DEFAULT_MAX_FILE_SIZE, DEFAULT_SUPPORTED_FORMATS))

    assert result["valid"] is True
    assert result["category"] == "documents"
    assert result["extension"] == ".txt"
    assert result["size"] > 0


def test_validation_service_rejects_large_file() -> None:
    service = ValidationService()
    big_data = b"0" * (DEFAULT_MAX_FILE_SIZE + 1)
    file_obj = io.BytesIO(big_data)
    file_obj.name = "oversized.pdf"  # type: ignore[attr-defined]
    file_obj.size = len(big_data)  # type: ignore[attr-defined]

    result = asyncio.run(service.validate_file(file_obj, DEFAULT_MAX_FILE_SIZE, DEFAULT_SUPPORTED_FORMATS))

    assert result["valid"] is False
    assert "grande" in (result["error"] or "")

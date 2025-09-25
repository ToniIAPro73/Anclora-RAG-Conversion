"""Configuration helpers for the advanced ingestion system."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

DEFAULT_SUPPORTED_FORMATS: Dict[str, List[str]] = {
    "documents": [".pdf", ".docx", ".doc", ".txt", ".md", ".rtf", ".odt"],
    "presentations": [".pptx", ".ppt", ".odp"],
    "spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "code": [".py", ".js", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".kt", ".swift"],
    "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "multimedia": [".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv"],
    "markup": [".html", ".xml", ".json", ".yaml", ".yml"],
}

DEFAULT_MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
DEFAULT_MARKDOWN_COLLECTION = "research_sources"


@dataclass(frozen=True)
class IngestionConfig:
    """Simple dataclass holding shared configuration values."""

    max_file_size: int = DEFAULT_MAX_FILE_SIZE
    supported_formats: Dict[str, List[str]] = field(default_factory=lambda: {k: list(v) for k, v in DEFAULT_SUPPORTED_FORMATS.items()})
    markdown_collection: str = DEFAULT_MARKDOWN_COLLECTION


def get_ingestion_config() -> IngestionConfig:
    """Return a new :class:IngestionConfig instance."""

    return IngestionConfig()


__all__ = ["IngestionConfig", "DEFAULT_SUPPORTED_FORMATS", "DEFAULT_MAX_FILE_SIZE", "DEFAULT_MARKDOWN_COLLECTION", "get_ingestion_config"]

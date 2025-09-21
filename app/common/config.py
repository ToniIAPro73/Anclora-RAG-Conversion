"""Application configuration helpers."""
from __future__ import annotations

from typing import List

# Default language for the application
DEFAULT_LANGUAGE: str = "es"

# Ordered list of supported language codes
_SUPPORTED_LANGUAGES: List[str] = [
    "es",
    "en",
]


def get_default_language() -> str:
    """Return the default language for the application."""
    return DEFAULT_LANGUAGE


def get_supported_languages() -> List[str]:
    """Return the list of supported language codes."""
    return list(_SUPPORTED_LANGUAGES)

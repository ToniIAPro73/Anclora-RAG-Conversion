"""Application configuration helpers."""
from __future__ import annotations

import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, List

import yaml

_DEFAULT_CONFIG: Dict[str, Any] = {
    "default_language": "es",
    "supported_languages": ["es", "en"],
}

_CONFIG_LOCK = threading.Lock()
_CACHED_CONFIG: Dict[str, Any] | None = None


def _config_path() -> Path:
    """Return the path to the YAML configuration file."""

    return Path(__file__).resolve().with_suffix(".yaml")


def _load_config() -> Dict[str, Any]:
    """Load configuration data from disk and cache the result."""

    global _CACHED_CONFIG
    with _CONFIG_LOCK:
        if _CACHED_CONFIG is not None:
            return _CACHED_CONFIG

        path = _config_path()
        data: Dict[str, Any] = {}

        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle) or {}
            if not isinstance(loaded, Mapping):
                raise ValueError("Configuration file must contain a mapping at the top level.")
            data = dict(loaded)

        config: Dict[str, Any] = {**_DEFAULT_CONFIG, **data}

        default_language = config.get("default_language")
        if not isinstance(default_language, str) or not default_language.strip():
            default_language = _DEFAULT_CONFIG["default_language"]
        default_language = default_language.strip()

        supported_languages_value = config.get("supported_languages")
        supported_languages: List[str] = []
        if isinstance(supported_languages_value, (list, tuple)):
            for language in supported_languages_value:
                if not isinstance(language, str):
                    continue
                cleaned = language.strip()
                if cleaned and cleaned not in supported_languages:
                    supported_languages.append(cleaned)

        if not supported_languages:
            supported_languages = list(_DEFAULT_CONFIG["supported_languages"])

        if default_language not in supported_languages:
            supported_languages.insert(0, default_language)

        _CACHED_CONFIG = {
            "default_language": default_language,
            "supported_languages": supported_languages,
        }

        return _CACHED_CONFIG


def reload_config() -> None:
    """Clear the cached configuration data."""

    global _CACHED_CONFIG
    with _CONFIG_LOCK:
        _CACHED_CONFIG = None


def get_default_language() -> str:
    """Return the default language for the application."""

    return str(_load_config()["default_language"])


def get_supported_languages() -> List[str]:
    """Return the list of supported language codes."""

    languages = _load_config()["supported_languages"]
    return list(languages)

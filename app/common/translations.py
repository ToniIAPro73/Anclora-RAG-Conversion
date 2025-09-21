"""Translation utilities for the Anclora AI RAG application."""
from __future__ import annotations

import os
import threading
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from .config import get_default_language, get_supported_languages

TRANSLATIONS_DIR_ENV_VAR = "ANCLORA_I18N_DIR"
"""Environment variable used to override the translation directory."""

_SUPPORTED_EXTENSIONS = (".yml", ".yaml")

_CACHE_LOCK = threading.Lock()
_CACHED_TRANSLATIONS: Dict[str, Dict[str, Any]] = {}
_CACHED_SIGNATURE: Tuple[Tuple[str, float], ...] | None = None
_CACHED_DIRECTORY: Path | None = None


def _resolve_translations_dir() -> Path:
    """Return the directory that stores translation files."""

    env_dir = os.environ.get(TRANSLATIONS_DIR_ENV_VAR)
    if env_dir:
        return Path(env_dir).expanduser()
    return Path(__file__).resolve().parent / "i18n"


def _list_translation_files(directory: Path) -> List[Path]:
    """Return a deterministic list of translation files in ``directory``."""

    if not directory.exists():
        return []

    files: Dict[str, Path] = {}
    for extension in _SUPPORTED_EXTENSIONS:
        for candidate in directory.glob(f"*{extension}"):
            try:
                resolved = candidate.resolve()
            except FileNotFoundError:
                continue
            if resolved.is_file():
                files[str(resolved)] = candidate

    return [files[key] for key in sorted(files)]


def _build_signature(files: Iterable[Path]) -> Tuple[Tuple[str, float], ...]:
    """Create a signature representing the state of the translation files."""

    signature: List[Tuple[str, float]] = []
    for file_path in files:
        try:
            mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            continue
        signature.append((str(file_path.resolve()), mtime))
    return tuple(sorted(signature))


def _load_translations_from_files(files: Iterable[Path]) -> Dict[str, Dict[str, Any]]:
    """Load translation dictionaries from ``files``."""

    loaded: Dict[str, Dict[str, Any]] = {}
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except FileNotFoundError:
            continue

        if not isinstance(data, Mapping):
            raise ValueError(
                f"Translation file {file_path} must contain a mapping at the top level."
            )

        loaded[file_path.stem] = {str(key): value for key, value in data.items()}

    return loaded


def _get_translations() -> Dict[str, Dict[str, Any]]:
    """Return cached translations, reloading them when files change."""

    directory = _resolve_translations_dir()

    with _CACHE_LOCK:
        files = _list_translation_files(directory)
        signature = _build_signature(files)

        global _CACHED_SIGNATURE, _CACHED_TRANSLATIONS, _CACHED_DIRECTORY
        if (
            _CACHED_DIRECTORY != directory
            or _CACHED_SIGNATURE != signature
            or not _CACHED_TRANSLATIONS
        ):
            _CACHED_TRANSLATIONS = _load_translations_from_files(files)
            _CACHED_SIGNATURE = signature
            _CACHED_DIRECTORY = directory

        return _CACHED_TRANSLATIONS


def get_text(key: str, lang: str | None = None, **kwargs: Any) -> str:
    """Return a localized string for ``key`` in the requested language."""

    translations = _get_translations()
    default_language = get_default_language()
    supported_languages = get_supported_languages()

    if not supported_languages:
        supported_languages = [default_language]

    if lang is None or lang not in supported_languages:
        lang = default_language

    language_code = lang if lang in translations else default_language
    language_translations = translations.get(language_code, {})
    default_translations = translations.get(default_language, {})

    text = language_translations.get(key)
    if text is None:
        text = default_translations.get(key, key)

    if kwargs and isinstance(text, str):
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting arguments are missing, fall back to the raw text.
            pass

    return str(text) if text is not None else key


def clear_translation_cache() -> None:
    """Clear the in-memory cache of translations."""

    with _CACHE_LOCK:
        global _CACHED_TRANSLATIONS, _CACHED_SIGNATURE, _CACHED_DIRECTORY
        _CACHED_TRANSLATIONS = {}
        _CACHED_SIGNATURE = None
        _CACHED_DIRECTORY = None

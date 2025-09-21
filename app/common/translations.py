"""Utility functions to load and access localized text for the application."""

from __future__ import annotations

import os
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import yaml


DEFAULT_LANGUAGE = "es"
"""Language code used when the requested language is not available."""

TRANSLATIONS_DIR_ENV_VAR = "ANCLORA_I18N_DIR"
"""Environment variable that overrides the default directory for translation files."""

_CACHE_LOCK = threading.Lock()
_CACHED_TRANSLATIONS: Dict[str, Dict[str, Any]] = {}
_CACHED_SIGNATURE: Tuple[Tuple[str, float], ...] | None = None
_CACHED_DIRECTORY: Path | None = None

_SUPPORTED_EXTENSIONS = (".yml", ".yaml")


def _resolve_translations_dir() -> Path:
    """Return the directory that stores translation files."""

    env_dir = os.environ.get(TRANSLATIONS_DIR_ENV_VAR)
    if env_dir:
        return Path(env_dir).expanduser()
    return Path(__file__).resolve().parent / "i18n"


def _list_translation_files(directory: Path) -> Iterable[Path]:
    """Yield translation files from ``directory`` that match supported extensions."""

    if not directory.exists():
        return []

    files: Dict[Path, Path] = {}
    for extension in _SUPPORTED_EXTENSIONS:
        for candidate in directory.glob(f"*{extension}"):
            try:
                resolved = candidate.resolve()
            except FileNotFoundError:
                continue
            if not resolved.is_file():
                continue
            files[resolved] = candidate
    return sorted(files.values())


def _build_signature(files: Iterable[Path]) -> Tuple[Tuple[str, float], ...]:
    """Create a signature representing the state of the translation files."""

    signature = []
    for file_path in files:
        try:
            mtime = file_path.stat().st_mtime
        except FileNotFoundError:
            continue
        signature.append((str(file_path.resolve()), mtime))
    return tuple(sorted(signature))


def _load_translations_from_files(files: Iterable[Path]) -> Dict[str, Dict[str, Any]]:
    """Load translation dictionaries from YAML files."""

    loaded: Dict[str, Dict[str, Any]] = {}
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except FileNotFoundError:
            # File may have been removed between discovery and reading; skip it.
            continue

        if not isinstance(data, Mapping):
            raise ValueError(f"Translation file {file_path} must contain a mapping at the top level.")

        loaded[file_path.stem] = {str(key): value for key, value in data.items()}

    return loaded


def _get_translations() -> Dict[str, Dict[str, Any]]:
    """Return cached translations, reloading them when files change."""

    directory = _resolve_translations_dir()

    with _CACHE_LOCK:
        files = list(_list_translation_files(directory))
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


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Return a localized string for ``key`` in the requested language."""

    translations = _get_translations()

    language = lang if lang in translations else DEFAULT_LANGUAGE
    text = translations.get(language, {}).get(key, key)

    if kwargs and isinstance(text, str):
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting arguments are missing, fall back to the raw text.
            pass

    return str(text) if text is not None else key


def clear_translation_cache() -> None:
    """Clear the in-memory cache of translations.

    Primarily useful for testing. The next call to :func:`get_text` will reload
    data from the YAML files.
    """

    with _CACHE_LOCK:
        global _CACHED_TRANSLATIONS, _CACHED_SIGNATURE, _CACHED_DIRECTORY
        _CACHED_TRANSLATIONS = {}
        _CACHED_SIGNATURE = None
        _CACHED_DIRECTORY = None

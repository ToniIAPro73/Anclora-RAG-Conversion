"""Translation utilities for the Anclora AI RAG application."""

from common.config import get_default_language, get_supported_languages

# Dictionary of translations for different languages
translations = {
    "es": {  # Spanish (default)
        # Common
        "app_title": "Anclora AI RAG",

        # Inicio.py
        "chat_placeholder": "Escribe tu mensaje :)",
        "empty_message_error": "Por favor, escribe un mensaje valido.",
        "long_message_error": "El mensaje es demasiado largo. Por favor, hazlo mas conciso (maximo 1000 caracteres).",
        "processing_message": "Procesando tu consulta...",

        # Archivos.py
        "files_title": "Archivos",
        "upload_file": "Cargar archivo",
        "add_to_knowledge_base": "Agregar archivo a la base de conocimiento",
        "processing_file": "Procesando archivo: {file_name}",
        "validation_error": "Error de validacion: {message}",
        "upload_warning": "Por favor carga al menos un archivo antes de agregarlo a la base de conocimiento.",
        "files_in_knowledge_base": "Archivos en la base de conocimiento:",
        "delete_file": "Eliminar archivo",
        "delete_from_knowledge_base": "Eliminar archivo de la base de conocimiento",
        "file_deleted": "Archivo eliminado con exito",
        "delete_error": "Ocurrio un error al eliminar el archivo: {error}",
        "one_file_at_a_time": "Solo se permite eliminar un archivo a la vez.",

        # Language selector
        "language_selector": "Idioma",
        "language_es": "Espanol",
        "language_en": "Ingles",

        # RAG responses
        "invalid_query": "Por favor, proporciona una consulta valida.",
        "long_query": "La consulta es demasiado larga. Por favor, hazla mas concisa.",
        "greeting_response": "Hola! Soy Bastet, tu asistente virtual de PBC. Estoy aqui para ayudarte con informacion sobre nuestros proyectos, productos y servicios. En que puedo asistirte hoy?",
        "no_documents": "Hola, soy Bastet de PBC. Actualmente no tengo documentos en mi base de conocimiento. Por favor, sube algunos documentos en la seccion 'Archivos' para que pueda ayudarte con informacion especifica. Mientras tanto, puedo contarte que PBC ofrece servicios de Ingenieria de Software e Inteligencia Artificial.",
        "no_context": "No se encontro informacion especifica en la base de conocimiento.",
        "processing_error": "Lo siento, ocurrio un error al procesar tu consulta. Por favor, intenta nuevamente o contacta al administrador si el problema persiste."
    },

    "en": {  # English
        # Common
        "app_title": "Anclora AI RAG",

        # Inicio.py
        "chat_placeholder": "Type your message :)",
        "empty_message_error": "Please write a valid message.",
        "long_message_error": "The message is too long. Please make it more concise (maximum 1000 characters).",
        "processing_message": "Processing your query...",

        # Archivos.py
        "files_title": "Files",
        "upload_file": "Upload file",
        "add_to_knowledge_base": "Add file to knowledge base",
        "processing_file": "Processing file: {file_name}",
        "validation_error": "Validation error: {message}",
        "upload_warning": "Please upload at least one file before adding it to the knowledge base.",
        "files_in_knowledge_base": "Files in knowledge base:",
        "delete_file": "Delete file",
        "delete_from_knowledge_base": "Delete file from knowledge base",
        "file_deleted": "File successfully deleted",
        "delete_error": "An error occurred while deleting the file: {error}",
        "one_file_at_a_time": "Only one file can be deleted at a time.",

        # Language selector
        "language_selector": "Language",
        "language_es": "Spanish",
        "language_en": "English",

        # RAG responses
        "invalid_query": "Please provide a valid query.",
        "long_query": "The query is too long. Please make it more concise.",
        "greeting_response": "Hello! I'm Bastet, your virtual assistant from PBC. I'm here to help you with information about our projects, products, and services. How can I assist you today?",
        "no_documents": "Hi, I'm Bastet from PBC. I don't have any documents in my knowledge base yet. Please upload some documents in the 'Files' section so I can help you with specific information. In the meantime, I can share that PBC offers Software Engineering and Artificial Intelligence services.",
        "no_context": "No specific information was found in the knowledge base.",
        "processing_error": "Sorry, an error occurred while processing your query. Please try again or contact the administrator if the problem persists."
    },
}


def get_text(key, lang=None, **kwargs):
    """
    Get the translated text for a given key and language.

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
    
    Returns:
        str: The translated text
    """
    default_language = get_default_language()
    supported_languages = get_supported_languages()

    if not supported_languages:
        supported_languages = [default_language]

    if default_language not in translations:
        translations.setdefault(default_language, {})

    if lang is None or lang not in supported_languages:
        lang = default_language

    language_translations = translations.get(lang, {})
    if not language_translations:
        language_translations = translations.get(default_language, {})
        lang = default_language

    # Get the translation for the key, or fall back to the default language
    text = language_translations.get(key)
    if text is None:
        text = translations.get(default_language, {}).get(key, key)

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

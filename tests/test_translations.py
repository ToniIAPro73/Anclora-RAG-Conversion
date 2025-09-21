from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.common import translations as translations_module
from app.common.config import get_default_language, get_supported_languages


def test_default_language_is_supported():
    default_language = get_default_language()
    supported_languages = get_supported_languages()

    assert default_language in supported_languages


def test_unsupported_language_falls_back_to_default():
    default_language = get_default_language()
    default_text = translations_module.get_text("app_title", default_language)

    # Request a language that is not part of the supported list
    assert translations_module.get_text("app_title", "fr") == default_text


def test_missing_translation_key_falls_back_to_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    translations_module.clear_translation_cache()

    es_file = tmp_path / "es.yml"
    es_file.write_text(
        "app_title: \"Anclora AI RAG\"\nfiles_title: \"Archivos\"\n",
        encoding="utf-8",
    )

    en_file = tmp_path / "en.yml"
    en_file.write_text(
        "app_title: \"Anclora AI RAG\"\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(translations_module.TRANSLATIONS_DIR_ENV_VAR, str(tmp_path))
    translations_module.clear_translation_cache()

    default_language = get_default_language()
    default_value = translations_module.get_text("files_title", default_language)

    assert translations_module.get_text("files_title", "en") == default_value

    translations_module.clear_translation_cache()

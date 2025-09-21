import importlib
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import common.translations as translations_module


@pytest.fixture
def translations(monkeypatch):
    """Reload the translations module with the default configuration."""

    monkeypatch.delenv("ANCLORA_I18N_DIR", raising=False)
    module = importlib.reload(translations_module)
    module.clear_translation_cache()
    return module


def test_returns_spanish_text(translations):
    """The loader returns the expected Spanish text with proper accents."""

    assert translations.get_text("empty_message_error", "es") == "Por favor, escribe un mensaje válido."
    assert translations.get_text("language_es", "es") == "Español"


def test_falls_back_to_default_language(translations):
    """Unsupported languages should fall back to the default locale."""

    assert translations.get_text("language_en", "fr") == translations.get_text("language_en", "es")


def test_allows_string_formatting(translations):
    """Formatted placeholders are interpolated when keyword arguments are provided."""

    result = translations.get_text("processing_file", "en", file_name="report.pdf")
    assert result == "Processing file: report.pdf"


def test_hot_reload_detects_file_changes(tmp_path, monkeypatch):
    """Modifying the YAML file should be reflected without restarting the process."""

    i18n_dir = tmp_path / "i18n"
    i18n_dir.mkdir()

    es_file = i18n_dir / "es.yml"
    en_file = i18n_dir / "en.yml"
    es_file.write_text("greeting: 'Hola'\n", encoding="utf-8")
    en_file.write_text("greeting: 'Hello'\n", encoding="utf-8")

    monkeypatch.setenv("ANCLORA_I18N_DIR", str(i18n_dir))
    module = importlib.reload(translations_module)
    module.clear_translation_cache()

    assert module.get_text("greeting", "es") == "Hola"

    # Ensure the modification time of the file changes on all platforms.
    time.sleep(0.1)
    es_file.write_text("greeting: 'Hola de nuevo'\n", encoding="utf-8")

    assert module.get_text("greeting", "es") == "Hola de nuevo"

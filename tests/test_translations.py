from copy import deepcopy
from pathlib import Path
import sys

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


def test_missing_translation_key_falls_back_to_default():
    default_language = get_default_language()
    default_value = translations_module.translations[default_language]["files_title"]

    backup = deepcopy(translations_module.translations["en"])
    try:
        translations_module.translations["en"].pop("files_title", None)
        assert translations_module.get_text("files_title", "en") == default_value
    finally:
        translations_module.translations["en"] = backup
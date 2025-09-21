"""Tests for Spanish translations and prompts."""

import sys
import types


def _install_langchain_stub() -> None:
    """Provide a minimal stub for ``langchain_core.prompts`` if needed."""

    if "langchain_core.prompts" in sys.modules:
        return

    langchain_core = types.ModuleType("langchain_core")
    prompts_module = types.ModuleType("langchain_core.prompts")

    class _FakeChatPromptTemplate:  # noqa: D401 - simple stub
        """Replacement that mimics the API used in tests."""

        @classmethod
        def from_messages(cls, messages):  # type: ignore[override]
            return messages

    prompts_module.ChatPromptTemplate = _FakeChatPromptTemplate
    langchain_core.prompts = prompts_module
    sys.modules["langchain_core"] = langchain_core
    sys.modules["langchain_core.prompts"] = prompts_module


_install_langchain_stub()

from app.common import assistant_prompt, translations

ACCENTED_CHARACTERS = set("áéíóúÁÉÍÓÚñÑ¡¿")


def contains_accented_character(value: str) -> bool:
    """Return True if the given value includes at least one accented character."""

    return any(character in ACCENTED_CHARACTERS for character in value)


def test_spanish_translations_have_accented_characters():
    """Critical Spanish translations must include accented characters."""

    spanish = translations.translations["es"]
    keys_with_expected_accents = (
        "language_es",
        "empty_message_error",
        "long_message_error",
        "validation_error",
        "processing_error",
    )

    for key in keys_with_expected_accents:
        value = spanish[key]
        assert contains_accented_character(
            value
        ), f"El valor de '{key}' debe contener tildes o eñes."


def test_spanish_prompt_contains_accented_characters():
    """The Spanish assistant prompt should use natural Spanish spelling."""

    assert contains_accented_character(
        assistant_prompt.ES_PROMPT
    ), "El prompt en español debe incluir caracteres acentuados."

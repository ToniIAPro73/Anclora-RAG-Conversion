"""Tests for helpers in ``app.common.langchain_module``."""

import pytest

from app.common.langchain_module import detect_language, response


@pytest.mark.parametrize(
    "text, expected",
    [
        ("¿Cuál es la situación energética actual en España?", "es"),
        ("What is the current energy policy status?", "en"),
        ("La reunión is tomorrow", "es"),
    ],
)
def test_detect_language_variants(text: str, expected: str) -> None:
    """The helper should detect supported languages while preserving tildes."""

    assert detect_language(text) == expected


@pytest.mark.parametrize(
    "query, expected_language, provided_language",
    [
        ("Hola, ¿cómo estás?", "es", None),
        ("Hola, ¿cómo estás?", "es", ""),
        ("Hello there", "en", None),
        ("Hello there", "en", ""),
    ],
)
def test_response_uses_detected_language_when_not_provided(
    monkeypatch: pytest.MonkeyPatch,
    query: str,
    expected_language: str,
    provided_language: str | None,
) -> None:
    """``response`` should fall back to detection for greetings when language is empty."""

    def fake_get_text(key: str, language: str) -> str:
        return f"{key}:{language}"

    monkeypatch.setattr("app.common.langchain_module.get_text", fake_get_text)

    result = response(query, language=provided_language)

    assert result == f"greeting_response:{expected_language}"

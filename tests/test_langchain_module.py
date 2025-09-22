"""Tests for helpers in ``app.common.langchain_module``."""

from types import SimpleNamespace

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


def test_response_long_greeting_invokes_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Consultas largas deben evitar la rama de saludos y ejecutar el flujo de RAG."""

    query = "Hola necesito el informe trimestral"

    def fake_get_text(key: str, language: str, **_: object) -> str:
        return f"{key}:{language}"

    monkeypatch.setattr("app.common.langchain_module.get_text", fake_get_text)
    monkeypatch.setattr(
        "app.common.langchain_module.parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
    )
    monkeypatch.setattr(
        "app.common.langchain_module.HuggingFaceEmbeddings",
        lambda model_name: SimpleNamespace(model_name=model_name),
    )
    monkeypatch.setattr(
        "app.common.langchain_module.record_rag_response",
        lambda *args, **kwargs: None,
    )

    class FakeCollection:
        def count(self) -> int:
            return 2

    fake_client = SimpleNamespace(
        get_collection=lambda name: FakeCollection(),
    )
    monkeypatch.setattr("app.common.langchain_module.CHROMA_SETTINGS", fake_client)

    class FakeRunnable:
        def __init__(self, func):
            self._func = func

        def invoke(self, value):
            return self._func(value)

        def __call__(self, value):
            return self._func(value)

        def __or__(self, other):
            if isinstance(other, FakeRunnable):
                return FakeRunnable(lambda value: other.invoke(self.invoke(value)))
            if callable(other):
                return FakeRunnable(lambda value: other(self.invoke(value)))
            return NotImplemented

        def __ror__(self, other):
            if isinstance(other, FakeRunnable):
                return FakeRunnable(lambda value: self.invoke(other.invoke(value)))
            if callable(other):
                return FakeRunnable(lambda value: self.invoke(other(value)))
            return NotImplemented

    class FakeRetriever:
        def __init__(self) -> None:
            self.queries: list[str] = []

        def __call__(self, rag_query: str):
            self.queries.append(rag_query)
            return [SimpleNamespace(page_content="Contexto simulado")]

        def __or__(self, formatter):
            return FakeRunnable(lambda rag_query: formatter(self(rag_query)))

    fake_retriever = FakeRetriever()

    class FakeChroma:
        def __init__(self, *_, **__):
            pass

        def as_retriever(self, **_):
            return fake_retriever

    monkeypatch.setattr("app.common.langchain_module.Chroma", FakeChroma)

    monkeypatch.setattr(
        "app.common.langchain_module.RunnablePassthrough",
        lambda: FakeRunnable(lambda value: value),
    )

    class FakePrompt:
        def __init__(self, language: str) -> None:
            self.language = language

        def __ror__(self, mapping):
            return FakeRunnable(
                lambda rag_query: {
                    "language": self.language,
                    "context": mapping["context"].invoke(rag_query),
                    "question": mapping["question"].invoke(rag_query),
                }
            )

    monkeypatch.setattr(
        "app.common.langchain_module.assistant_prompt",
        lambda language: FakePrompt(language),
    )

    class FakeLLM:
        def __ror__(self, previous):
            return FakeRunnable(
                lambda rag_query: f"fake_llm_response:{previous.invoke(rag_query)['question']}"
            )

    monkeypatch.setattr(
        "app.common.langchain_module.Ollama",
        lambda *args, **kwargs: FakeLLM(),
    )

    class FakeParser:
        def __ror__(self, previous):
            return FakeRunnable(lambda rag_query: previous.invoke(rag_query))

    monkeypatch.setattr(
        "app.common.langchain_module.StrOutputParser",
        lambda: FakeParser(),
    )

    result = response(query)

    assert result == "fake_llm_response:Hola necesito el informe trimestral"
    assert fake_retriever.queries == [query]

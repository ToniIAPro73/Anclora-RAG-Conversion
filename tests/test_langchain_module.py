"""Tests for helpers in ``app.common.langchain_module``."""

from threading import Lock
from types import SimpleNamespace

import pytest

from app.common.langchain_module import detect_language, response


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


class FakePrompt:
    def __init__(self, language: str) -> None:
        self.language = language
        self.last_context: str | None = None
        self.last_question: str | None = None

    def __ror__(self, mapping):
        def _runner(rag_query: str):
            context = mapping["context"].invoke(rag_query)
            question = mapping["question"].invoke(rag_query)
            self.last_context = context
            self.last_question = question
            return {
                "language": self.language,
                "context": context,
                "question": question,
            }

        return FakeRunnable(_runner)


class FakeLLM:
    def __ror__(self, previous):
        return FakeRunnable(
            lambda rag_query: f"fake_llm_response:{previous.invoke(rag_query)['question']}"
        )


class FakeParser:
    def __ror__(self, previous):
        return FakeRunnable(lambda rag_query: previous.invoke(rag_query))


def _configure_rag_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    embeddings_factory,
    docs_by_collection: dict[str, list[tuple[str, float]]] | None = None,
) -> tuple[dict[str, object], list[object], list[FakePrompt]]:
    def fake_get_text(key: str, language: str, **_: object) -> str:
        return f"{key}:{language}"

    monkeypatch.setattr("app.common.langchain_module.get_text", fake_get_text)
    monkeypatch.setattr(
        "app.common.langchain_module.parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
    )
    monkeypatch.setattr(
        "app.common.langchain_module.record_rag_response",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.HuggingFaceEmbeddings", embeddings_factory
    )

    docs_by_collection = docs_by_collection or {
        "conversion_rules": [("Contexto simulado", 0.1)],
    }

    monkeypatch.setattr(
        "app.common.langchain_module.CHROMA_COLLECTIONS",
        {
            name: SimpleNamespace(domain=name, description=name)
            for name in docs_by_collection
        },
    )

    monkeypatch.setattr("app.common.langchain_module._collections_cache", {})
    monkeypatch.setattr("app.common.langchain_module._collections_lock", Lock())

    class FakeCollection:
        def __init__(self, name: str) -> None:
            self.name = name

        def count(self) -> int:
            return len(docs_by_collection.get(self.name, []))

    fake_client = SimpleNamespace(
        get_collection=lambda name: FakeCollection(name),
    )
    monkeypatch.setattr("app.common.langchain_module.CHROMA_SETTINGS", fake_client)

    vectorstores: dict[str, object] = {}
    chroma_embeddings: list[object] = []

    class FakeChroma:
        def __init__(
            self,
            *,
            collection_name: str,
            embedding_function=None,
            **__: object,
        ) -> None:
            self.collection_name = collection_name
            self.embedding = embedding_function
            self.queries: list[tuple[str, int]] = []
            vectorstores[self.collection_name] = self
            chroma_embeddings.append(embedding_function)

        def similarity_search_with_score(
            self, query: str, k: int, **__: object
        ) -> list[tuple[SimpleNamespace, float]]:
            self.queries.append((query, k))
            results: list[tuple[SimpleNamespace, float]] = []
            for content, score in docs_by_collection.get(self.collection_name, []):
                results.append(
                    (
                        SimpleNamespace(
                            page_content=content,
                            metadata={"collection": self.collection_name},
                        ),
                        score,
                    )
                )
            return results[:k]

    monkeypatch.setattr("app.common.langchain_module.Chroma", FakeChroma)
    monkeypatch.setattr(
        "app.common.langchain_module.RunnableLambda",
        lambda func: FakeRunnable(func),
    )
    monkeypatch.setattr(
        "app.common.langchain_module.RunnablePassthrough",
        lambda: FakeRunnable(lambda value: value),
    )

    created_prompts: list[FakePrompt] = []

    def _fake_prompt_factory(language: str) -> FakePrompt:
        prompt = FakePrompt(language)
        created_prompts.append(prompt)
        return prompt

    monkeypatch.setattr(
        "app.common.langchain_module.assistant_prompt",
        _fake_prompt_factory,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.Ollama", lambda *args, **kwargs: FakeLLM()
    )
    monkeypatch.setattr(
        "app.common.langchain_module.StrOutputParser", lambda: FakeParser()
    )

    return vectorstores, chroma_embeddings, created_prompts


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
    monkeypatch.setattr("app.common.langchain_module._embeddings_instance", None)

    vectorstores, _, _ = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=lambda model_name: SimpleNamespace(model_name=model_name),
    )

    result = response(query)

    assert result == "fake_llm_response:Hola necesito el informe trimestral"
    assert all(
        [stored_query for stored_query, _ in store.queries] == [query]
        for store in vectorstores.values()
    )


def test_response_reuses_embeddings_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """El helper ``get_embeddings`` debe inicializar el modelo una única vez."""

    query = "Hola necesito el informe trimestral"
    monkeypatch.setattr("app.common.langchain_module._embeddings_instance", None)

    instantiations: list[str] = []

    def fake_embeddings(model_name: str):
        instantiations.append(model_name)
        return SimpleNamespace(model_name=model_name)

    vectorstores, chroma_embeddings, _ = _configure_rag_environment(
        monkeypatch, embeddings_factory=fake_embeddings
    )

    first_result = response(query)
    second_result = response(query)

    assert first_result == "fake_llm_response:Hola necesito el informe trimestral"
    assert second_result == "fake_llm_response:Hola necesito el informe trimestral"
    assert len(instantiations) == 1
    assert len(chroma_embeddings) == 1
    store = next(iter(vectorstores.values()))
    assert store.embedding is chroma_embeddings[0]
    assert [stored_query for stored_query, _ in store.queries] == [query, query]


@pytest.mark.parametrize(
    "docs_by_collection, expected_snippet",
    [
        (
            {
                "conversion_rules": [("Manual de conversión detallado", 0.05)],
                "troubleshooting": [],
            },
            "Manual de conversión detallado",
        ),
        (
            {
                "conversion_rules": [],
                "troubleshooting": [
                    ("Procedimiento de diagnóstico crítico", 0.02),
                ],
            },
            "Procedimiento de diagnóstico crítico",
        ),
    ],
)
def test_response_retrieves_from_any_collection(
    monkeypatch: pytest.MonkeyPatch,
    docs_by_collection: dict[str, list[tuple[str, float]]],
    expected_snippet: str,
) -> None:
    """``response`` debe utilizar la colección disponible sin declarar la base vacía."""

    monkeypatch.setattr("app.common.langchain_module._embeddings_instance", None)

    _, _, prompts = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=lambda model_name: SimpleNamespace(model_name=model_name),
        docs_by_collection=docs_by_collection,
    )

    result = response("Necesito asistencia técnica")

    assert result == "fake_llm_response:Necesito asistencia técnica"
    assert prompts
    assert expected_snippet in (prompts[-1].last_context or "")


def test_response_combines_documents_across_collections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El contexto debe incluir fragmentos de todas las colecciones con documentos."""

    monkeypatch.setattr("app.common.langchain_module._embeddings_instance", None)

    docs = {
        "conversion_rules": [("Guía de conversión avanzada", 0.04)],
        "troubleshooting": [("Checklist de soporte urgente", 0.03)],
    }

    _, _, prompts = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=lambda model_name: SimpleNamespace(model_name=model_name),
        docs_by_collection=docs,
    )

    result = response("Requiero documentación técnica")

    assert result == "fake_llm_response:Requiero documentación técnica"
    context = prompts[-1].last_context or ""
    assert "Guía de conversión avanzada" in context
    assert "Checklist de soporte urgente" in context

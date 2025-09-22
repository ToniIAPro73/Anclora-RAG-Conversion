"""Tests for helpers in ``app.common.langchain_module``."""

from threading import Lock
from types import SimpleNamespace

import pytest

from app.common.constants import CHROMA_COLLECTIONS
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

class FakeRetriever:
    def __init__(self, collection_name: str, documents: list[SimpleNamespace]) -> None:
        self.collection_name = collection_name
        self._documents = documents
        self.queries: list[str] = []

    def invoke(self, rag_query: str):
        return self.__call__(rag_query)

    def __call__(self, rag_query: str):
        self.queries.append(rag_query)
        copied_documents: list[SimpleNamespace] = []
        for doc in self._documents:
            metadata = getattr(doc, "metadata", None)
            copied_documents.append(
                SimpleNamespace(
                    page_content=getattr(doc, "page_content", "Contexto simulado"),
                    metadata=dict(metadata) if isinstance(metadata, dict) else {},
                )
            )
        return copied_documents

    def __or__(self, formatter):
        return FakeRunnable(lambda rag_query: formatter(self(rag_query)))

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
    collection_counts: dict[str, int] | None = None,
    collection_documents: dict[str, list[SimpleNamespace]] | None = None,
) -> tuple[list[FakeRetriever], list[object]]:

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

    if collection_counts is None:
        counts_by_collection = {name: 2 for name in CHROMA_COLLECTIONS}
    else:
        counts_by_collection = dict(collection_counts)
        for name in CHROMA_COLLECTIONS:
            counts_by_collection.setdefault(name, 0)

    if collection_documents is None:
        documents_by_collection = {
            name: [
                SimpleNamespace(
                    page_content=f"Contexto simulado {name}",
                    metadata={"distance": float(index)},
                )
            ]
            for index, name in enumerate(CHROMA_COLLECTIONS)
        }
    else:
        documents_by_collection = {
            name: list(docs)
            for name, docs in collection_documents.items()
        }

    def _documents_for(collection_name: str) -> list[SimpleNamespace]:
        docs = documents_by_collection.get(collection_name)
        if docs:
            return docs
        return [
            SimpleNamespace(
                page_content=f"Contexto simulado {collection_name}",
                metadata={"distance": 0.0},
            )
        ]

    class FakeCollection:
        def __init__(self, name: str) -> None:
            self._name = name

        def count(self) -> int:
            return counts_by_collection.get(self._name, 0)

    fake_client = SimpleNamespace(
        get_collection=lambda name: FakeCollection(name),
    )
    monkeypatch.setattr("app.common.langchain_module.CHROMA_SETTINGS", fake_client)

    vectorstores: dict[str, object] = {}
    chroma_embeddings: list[object] = []

    class FakeChroma:
        def __init__(
            self,
            *_,
            collection_name: str | None = None,
            embedding_function=None,
            **__,
        ):
            name = collection_name or "vectordb"
            self.retriever = FakeRetriever(name, _documents_for(name))
            created_retrievers.append(self.retriever)
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
    monkeypatch.setattr(
        "app.common.langchain_module.RunnableLambda",
        lambda func: FakeRunnable(func),
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
    assert len(retrievers) == len(CHROMA_COLLECTIONS)
    assert all(retriever.queries == [query] for retriever in retrievers)
    assert {
        retriever.collection_name for retriever in retrievers
    } == set(CHROMA_COLLECTIONS)

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
    expected_instances = len(CHROMA_COLLECTIONS) * 2
    assert len(chroma_embeddings) == expected_instances
    assert len(retrievers) == expected_instances
    assert all(embedding is chroma_embeddings[0] for embedding in chroma_embeddings)
    assert all(retriever.queries == [query] for retriever in retrievers)


def test_response_uses_documents_from_additional_collections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cuando ``vectordb`` está vacío se deben usar otras colecciones disponibles."""

    query = "Necesito material multimedia para la campaña"
    monkeypatch.setattr("app.common.langchain_module._embeddings_instance", None)

    retrievers, _ = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=lambda model_name: SimpleNamespace(model_name=model_name),
        collection_counts={
            "conversion_rules": 0,
            "troubleshooting": 0,
            "multimedia_assets": 1,
            "vectordb": 0,
        },
        collection_documents={
            "multimedia_assets": [
                SimpleNamespace(
                    page_content="Documento multimedia",
                    metadata={"distance": 0.05},
                )
            ]
        },
    )

    result = response(query)

    assert result == "fake_llm_response:Necesito material multimedia para la campaña"
    assert len(retrievers) == 1
    assert retrievers[0].collection_name == "multimedia_assets"
    assert retrievers[0].queries == [query]

"""Tests for helpers in ``app.common.langchain_module``."""

import sys
from threading import Lock
from types import SimpleNamespace

import pytest

from app.common.constants import CHROMA_COLLECTIONS
from app.common.langchain_module import LegalComplianceGuardError, detect_language, response


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
    domain_models: dict[str, str] | None = None,
):
    """Configure the environment to exercise the RAG pipeline in tests."""

    import importlib
    from tests import conftest as test_conftest

    if hasattr(test_conftest, "_install_langchain_stubs"):
        test_conftest._install_langchain_stubs()
    if hasattr(test_conftest, "_install_common_stubs"):
        test_conftest._install_common_stubs()

    langchain_module = importlib.reload(
        importlib.import_module("app.common.langchain_module")
    )
    globals()["response"] = langchain_module.response
    globals()["detect_language"] = langchain_module.detect_language

    def fake_get_text(key: str, language: str, **_: object) -> str:
        return f"{key}:{language}"

    monkeypatch.setattr(langchain_module, "get_text", fake_get_text)
    monkeypatch.setattr(
        langchain_module,
        "parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
    )
    monkeypatch.setattr(
        langchain_module,
        "record_rag_response",
        lambda *args, **kwargs: None,
    )

    domain_map: dict[str, str] = {"__default__": "all-MiniLM-L6-v2"}
    if domain_models:
        for domain, model in domain_models.items():
            key = (domain or "").strip().lower() or "__default__"
            domain_map[key] = model

    class _StubManager:
        def __init__(self) -> None:
            self._lock = Lock()
            self._domain_cache: dict[str, object] = {}
            self._model_cache: dict[str, object] = {}
            self.requests: list[str | None] = []

        def get_embeddings(self, domain: str | None = None):
            key = (domain or "").strip().lower() or "__default__"
            self.requests.append(domain)
            cached = self._domain_cache.get(key)
            if cached is not None:
                return cached
            with self._lock:
                cached = self._domain_cache.get(key)
                if cached is None:
                    model_name = domain_map.get(key, domain_map["__default__"])
                    instance = self._model_cache.get(model_name)
                    if instance is None:
                        instance = embeddings_factory(model_name=model_name)
                        self._model_cache[model_name] = instance
                    self._domain_cache[key] = instance
                    cached = instance
            return cached

    manager = _StubManager()
    monkeypatch.setattr(langchain_module, "get_embeddings_manager", lambda: manager)
    monkeypatch.setattr(langchain_module, "_collections_cache", {}, raising=False)

    if collection_counts is None:
        counts_by_collection = {name: 2 for name in CHROMA_COLLECTIONS}
    else:
        counts_by_collection = dict(collection_counts)
        for name in CHROMA_COLLECTIONS:
            counts_by_collection.setdefault(name, 0)

    monkeypatch.setattr(
        langchain_module,
        "_get_collection_document_count",
        lambda name: counts_by_collection.get(name, 0),
    )

    if collection_documents is None:
        documents_by_collection: dict[str, list[SimpleNamespace]] = {}
        for index, name in enumerate(CHROMA_COLLECTIONS):
            metadata = {"distance": float(index)}
            if name == "legal_compliance":
                metadata.update(
                    {
                        "policy_id": "default_policy",
                        "policy_version": "v1",
                        "collection": "legal_compliance",
                    }
                )
            documents_by_collection[name] = [
                SimpleNamespace(
                    page_content=f"Contexto simulado {name}",
                    metadata=metadata,
                )
            ]
    else:
        documents_by_collection = {
            name: list(docs)
            for name, docs in collection_documents.items()
        }

    def _documents_for(collection_name: str) -> list[SimpleNamespace]:
        docs = documents_by_collection.get(collection_name)
        if docs:
            return docs
        metadata = {"distance": 0.0}
        if collection_name == "legal_compliance":
            metadata.update(
                {
                    "policy_id": "fallback_policy",
                    "policy_version": "v1",
                    "collection": "legal_compliance",
                }
            )
        return [
            SimpleNamespace(
                page_content=f"Contexto simulado {collection_name}",
                metadata=metadata,
            )
        ]

    collection_requests: list[str] = []

    class FakeCollection:
        def __init__(self, name: str) -> None:
            self._name = name

        def count(self) -> int:
            return counts_by_collection.get(self._name, 0)

    def _get_collection(name: str) -> FakeCollection:
        collection_requests.append(name)
        return FakeCollection(name)

    fake_client = SimpleNamespace(get_collection=_get_collection)
    monkeypatch.setattr(langchain_module, "CHROMA_SETTINGS", fake_client)

    created_retrievers: list[FakeRetriever] = []
    chroma_embeddings: list[tuple[str, object]] = []

    class FakeChroma:
        def __init__(
            self,
            *_,
            collection_name: str | None = None,
            embedding_function=None,
            **__,
        ) -> None:
            name = collection_name or "vectordb"
            self.collection_name = name
            self.embedding_function = embedding_function
            self.retriever = FakeRetriever(name, _documents_for(name))
            self.collection_name = name
            self.queries: list[tuple[str, int]] = []
            created_retrievers.append(self.retriever)
            
            chroma_embeddings.append((name, embedding_function))

        def as_retriever(self, *_, **__):  # noqa: D401 - parity with real API
            return self.retriever

    monkeypatch.setattr(langchain_module, "Chroma", FakeChroma)
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

    return created_retrievers, chroma_embeddings, created_prompts, manager, collection_requests

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

    retrievers, _, _, manager, collection_requests = _configure_rag_environment(

        monkeypatch,
        embeddings_factory=lambda *, model_name: SimpleNamespace(model_name=model_name),
    )

    result = response(query)

    assert result == "fake_llm_response:Hola necesito el informe trimestral"
    assert len(retrievers) == len(CHROMA_COLLECTIONS)
    assert all(retriever.queries == [query] for retriever in retrievers)
    assert {retriever.collection_name for retriever in retrievers} == set(
        CHROMA_COLLECTIONS
    )
    requested_domains = {request for request in manager.requests if request}
    assert requested_domains == {config.domain for config in CHROMA_COLLECTIONS.values()}
    assert collection_requests == list(CHROMA_COLLECTIONS)

def test_response_reuses_embeddings_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """El helper ``get_embeddings`` debe inicializar el modelo una única vez."""

    query = "Hola necesito el informe trimestral"
    instantiations: list[str] = []

    def fake_embeddings(*, model_name: str):
        instantiations.append(model_name)
        return SimpleNamespace(model_name=model_name)

    domain_models = {
        "documents": "sentence-transformers/all-MiniLM-L6-v2",
        "code": "sentence-transformers/all-mpnet-base-v2",
        "multimedia": "intfloat/multilingual-e5-large",
    }

    retrievers, chroma_embeddings, _, manager, collection_requests = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=fake_embeddings,
        domain_models=domain_models,
    )

    first_result = response(query)
    second_result = response(query)

    assert first_result == "fake_llm_response:Hola necesito el informe trimestral"
    assert second_result == "fake_llm_response:Hola necesito el informe trimestral"
    assert len(instantiations) == len(domain_models)
    assert set(instantiations) == set(domain_models.values())
    assert len(chroma_embeddings) == len(CHROMA_COLLECTIONS)
    for collection_name, embedding in chroma_embeddings:
        assert embedding.model_name == domain_models[
            CHROMA_COLLECTIONS[collection_name].domain
        ]
    assert len(retrievers) == len(CHROMA_COLLECTIONS)
    assert all(retriever.queries == [query, query] for retriever in retrievers)
    assert {request for request in manager.requests if request} == {
        config.domain for config in CHROMA_COLLECTIONS.values()
    }
    expected_collections = list(CHROMA_COLLECTIONS)
    assert collection_requests == expected_collections * 2

def test_response_uses_documents_from_additional_collections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cuando ``vectordb`` está vacío se deben usar otras colecciones disponibles."""

    query = "Necesito material multimedia para la campaña"

    retrievers, chroma_embeddings, _, manager, collection_requests = _configure_rag_environment(
        monkeypatch,
        embeddings_factory=lambda *, model_name: SimpleNamespace(model_name=model_name),
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
    assert chroma_embeddings[0][0] == "multimedia_assets"
    assert chroma_embeddings[0][1].model_name == "all-MiniLM-L6-v2"
    assert len(chroma_embeddings) == 1
    assert manager.requests == ["multimedia"]
    assert collection_requests == ["conversion_rules", "troubleshooting", "multimedia_assets"]
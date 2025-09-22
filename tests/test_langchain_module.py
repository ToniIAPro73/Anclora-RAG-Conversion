"""Tests for helpers in ``app.common.langchain_module``."""

from types import SimpleNamespace

import pytest

from app.common.constants import CHROMA_COLLECTIONS

langchain_module = None
response = None
detect_language = None


@pytest.fixture(autouse=True)
def _reload_langchain_module(monkeypatch):
    import importlib
    import sys
    import types

    class _StubStreamingHandler:
        def __init__(self, *args, **kwargs) -> None:
            pass

    class _StubEmbeddings:
        def __init__(self, *args, **kwargs) -> None:
            pass

    class _StubLLM:
        def __init__(self, *args, **kwargs) -> None:
            pass

    class _StubParser:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def invoke(self, value):  # pragma: no cover - defensive stub
            return value

        def __call__(self, value):  # pragma: no cover - defensive stub
            return value

    def _stub_passthrough():  # pragma: no cover - replaced in tests
        raise AssertionError("RunnablePassthrough stub should be patched in tests")

    stubbed_modules = {
        "langchain": {},
        "langchain.chains": {"RetrievalQA": object()},
        "langchain.callbacks": {},
        "langchain.callbacks.streaming_stdout": {
            "StreamingStdOutCallbackHandler": _StubStreamingHandler
        },
        "langchain_community": {},
        "langchain_community.embeddings": {"HuggingFaceEmbeddings": _StubEmbeddings},
        "langchain_community.llms": {"Ollama": _StubLLM},
        "langchain_core": {},
        "langchain_core.output_parsers": {"StrOutputParser": _StubParser},
        "langchain_core.runnables": {"RunnablePassthrough": _stub_passthrough},
    }

    for module_name, attributes in stubbed_modules.items():
        module = types.ModuleType(module_name)
        if "." not in module_name:
            module.__path__ = []  # type: ignore[attr-defined]
        for attr_name, attr_value in attributes.items():
            setattr(module, attr_name, attr_value)
        monkeypatch.setitem(sys.modules, module_name, module)
        parent_name, _, child_name = module_name.rpartition(".")
        if parent_name:
            parent_module = sys.modules.get(parent_name)
            if parent_module is None:
                parent_module = types.ModuleType(parent_name)
                parent_module.__path__ = []  # type: ignore[attr-defined]
                monkeypatch.setitem(sys.modules, parent_name, parent_module)
            elif not hasattr(parent_module, "__path__"):
                setattr(parent_module, "__path__", [])
            monkeypatch.setattr(parent_module, child_name, module, raising=False)

    common_pkg = sys.modules.get("common")
    if common_pkg is None:
        common_pkg = types.ModuleType("common")
        common_pkg.__path__ = []  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "common", common_pkg)
    elif not hasattr(common_pkg, "__path__"):
        setattr(common_pkg, "__path__", [])

    for submodule in (
        "observability",
        "constants",
        "assistant_prompt",
        "translations",
        "text_normalization",
        "chroma_db_settings",
    ):
        if submodule == "chroma_db_settings":
            chroma_stub = types.ModuleType("common.chroma_db_settings")

            class _PlaceholderChroma:
                def __init__(self, *args, **kwargs) -> None:
                    pass

            chroma_stub.Chroma = _PlaceholderChroma
            monkeypatch.setitem(sys.modules, "common.chroma_db_settings", chroma_stub)
            monkeypatch.setattr(common_pkg, submodule, chroma_stub, raising=False)
            continue

        module = importlib.import_module(f"app.common.{submodule}")
        monkeypatch.setitem(sys.modules, f"common.{submodule}", module)
        monkeypatch.setattr(common_pkg, submodule, module, raising=False)

    module = importlib.import_module("app.common.langchain_module")
    module = importlib.reload(module)

    globals()["langchain_module"] = module
    globals()["response"] = module.response
    globals()["detect_language"] = module.detect_language

    yield

    module = importlib.reload(module)
    globals()["langchain_module"] = module
    globals()["response"] = module.response
    globals()["detect_language"] = module.detect_language

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

) -> tuple[list[FakeRetriever], list[object], list[FakePrompt]]:

    def fake_get_text(key: str, language: str, **_: object) -> str:
        return f"{key}:{language}"

    monkeypatch.setattr(langchain_module, "get_text", fake_get_text)
    monkeypatch.setattr(
        langchain_module,
        "get_text",
        fake_get_text,
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
    )
    monkeypatch.setattr(
        langchain_module,
        "parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.record_rag_response",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        langchain_module,
        "record_rag_response",
        lambda *args, **kwargs: None,
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.HuggingFaceEmbeddings", embeddings_factory
    )
    monkeypatch.setattr(
        langchain_module,
        "HuggingFaceEmbeddings",
        embeddings_factory,
        raising=False,
    )

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

    original_client = langchain_module.CHROMA_SETTINGS
    monkeypatch.setattr(
        original_client,
        "get_collection",
        lambda name: FakeCollection(name),
        raising=False,
    )
    monkeypatch.setattr("app.common.langchain_module.CHROMA_SETTINGS", original_client)

    chroma_embeddings: list[object] = []
    created_retrievers: list[FakeRetriever] = []

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
            self.retriever = FakeRetriever(name, _documents_for(name))
            self.collection_name = name
            self.queries: list[tuple[str, int]] = []
            created_retrievers.append(self.retriever)
            chroma_embeddings.append(embedding_function)
            self.queries: list[tuple[str, int]] = []

        def as_retriever(self, **kwargs):
            self.retriever.queries.clear()
            return self.retriever

        def similarity_search_with_score(
            self, query: str, k: int, **__: object
        ) -> list[tuple[SimpleNamespace, float]]:
            self.queries.append((query, k))
            results: list[tuple[SimpleNamespace, float]] = []
            for doc in _documents_for(self.collection_name)[:k]:
                base_metadata = {}
                original_metadata = getattr(doc, "metadata", {})
                if isinstance(original_metadata, dict):
                    base_metadata.update(original_metadata)
                base_metadata.setdefault("collection", self.collection_name)
                distance = 0.0
                if isinstance(original_metadata, dict) and "distance" in original_metadata:
                    distance = float(original_metadata["distance"])
                results.append(
                    (
                        SimpleNamespace(
                            page_content=getattr(doc, "page_content", "Contexto simulado"),
                            metadata=base_metadata,
                        ),
                        distance,
                    )
                )
            return results

    monkeypatch.setattr("app.common.langchain_module.Chroma", FakeChroma)
    monkeypatch.setattr(langchain_module, "Chroma", FakeChroma, raising=False)
    monkeypatch.setattr(
        "app.common.langchain_module.RunnableLambda",
        lambda func: FakeRunnable(func),
    )
    monkeypatch.setattr(
        langchain_module,
        "RunnableLambda",
        lambda func: FakeRunnable(func),
        raising=False,
    )
    passthrough = lambda: FakeRunnable(lambda value: value)
    monkeypatch.setattr(
        "app.common.langchain_module.RunnablePassthrough",
        passthrough,
    )
    monkeypatch.setattr(
        langchain_module,
        "RunnablePassthrough",
        passthrough,
        raising=False,
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
        langchain_module,
        "assistant_prompt",
        _fake_prompt_factory,
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.Ollama", lambda *args, **kwargs: FakeLLM()
    )
    monkeypatch.setattr(
        langchain_module,
        "Ollama",
        lambda *args, **kwargs: FakeLLM(),
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.StrOutputParser", lambda: FakeParser()
    )

    monkeypatch.setattr(
        langchain_module,
        "StrOutputParser",
        lambda: FakeParser(),
        raising=False,
    )
    monkeypatch.setattr(
        "app.common.langchain_module.RunnableLambda",
        lambda func: FakeRunnable(func),
    )
    monkeypatch.setattr(
        langchain_module,
        "RunnableLambda",
        lambda func: FakeRunnable(func),
        raising=False,
    )

    return created_retrievers, chroma_embeddings, created_prompts

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

    retrievers, _, _ = _configure_rag_environment(
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

    retrievers, chroma_embeddings, _ = _configure_rag_environment(
        monkeypatch, embeddings_factory=fake_embeddings
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

    retrievers, _, _ = _configure_rag_environment(
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
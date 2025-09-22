"""Regression tests for the public ``response`` helper."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Dict, List, Optional

import pytest

from app.common.text_normalization import normalize_to_nfc
from tests.common.rag_mocks import (
    FakeDoc,
    FakeEmbeddings,
    FakeLLM,
    FakeParser,
    FakeRetriever,
    FakeRunnable,
    FakeStreamingHandler,
    build_prompt_builders,
)


class _Harness:
    """Configurable harness that captures the behaviour of the RAG pipeline."""

    def __init__(self) -> None:
        self.llm_callback: Callable[[dict], str] | None = None
        self.prompt_inputs: List[dict] = []
        self.llm_invocations: List[dict] = []
        self.retriever_kwargs: Dict[str, object] | None = None
        self.collection_docs: Dict[str, List[FakeDoc]] = {}
        self.default_docs: List[FakeDoc] = [FakeDoc("Contexto simulado.")]
        self.collection_counts: Dict[str, int] = {}
        self.metric_events: List[dict] = []
        self.prompt_variants: List[str] = []
        self.selected_collections: List[str] = []
        self.retrievers: List[FakeRetriever] = []

    def reset_tracking(self) -> None:
        """Clear runtime observations collected during a test."""

        self.prompt_inputs.clear()
        self.llm_invocations.clear()
        self.retriever_kwargs = None
        self.metric_events.clear()
        self.prompt_variants.clear()
        self.selected_collections.clear()
        self.retrievers.clear()

    def set_docs(self, *contents: str) -> None:
        """Configure the documents returned when a collection has no override."""

        self.default_docs = [FakeDoc(text) for text in contents] if contents else []
        self.collection_counts.clear()

    def set_docs_for(self, collection: str, *contents: str) -> None:
        """Configure documents specific to *collection*."""

        self.collection_docs[collection] = [FakeDoc(text) for text in contents]
        self.collection_counts[collection] = len(self.collection_docs[collection])

    def docs_for(self, collection: str) -> List[FakeDoc]:
        docs = self.collection_docs.get(collection)
        if docs is not None:
            return docs
        return self.default_docs

    def document_count(self, collection: str) -> int:
        if collection in self.collection_counts:
            return self.collection_counts[collection]
        docs = self.collection_docs.get(collection)
        count = len(docs) if docs is not None else len(self.default_docs)
        self.collection_counts[collection] = count
        return count

    def set_llm_callback(self, callback: Callable[[dict], str]) -> None:
        self.llm_callback = callback

    def run_llm(self, payload: dict) -> str:
        self.llm_invocations.append(payload)
        if self.llm_callback is None:
            raise AssertionError("LLM callback was not configured for the test case.")
        return self.llm_callback(payload)

    def record_prompt(self, payload: dict) -> None:
        self.prompt_inputs.append(payload)
        variant = payload.get("prompt_variant")
        if isinstance(variant, str):
            self.prompt_variants.append(variant)

    def record_metrics(self, language: str, status: str, **kwargs: object) -> None:
        event = {"language": language, "status": status, "kwargs": kwargs}
        self.metric_events.append(event)
        documents = kwargs.get("collection_documents")
        if isinstance(documents, dict):
            self.selected_collections = list(documents.keys())


@pytest.fixture
def rag_test_harness(monkeypatch: pytest.MonkeyPatch):
    """Patch the langchain module so ``response`` can run without external services."""

    project_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(project_root / "app"))

    stubbed_modules = {
        "langchain": {},
        "langchain.chains": {"RetrievalQA": object()},
        "langchain.callbacks": {},
        "langchain.callbacks.streaming_stdout": {"StreamingStdOutCallbackHandler": object()},
        "langchain_community": {},
        "langchain_community.embeddings": {"HuggingFaceEmbeddings": object()},
        "langchain_community.llms": {"Ollama": object()},
        "langchain_core": {},
        "langchain_core.output_parsers": {"StrOutputParser": object()},
        "langchain_core.runnables": {"RunnablePassthrough": object()},
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

    constants_stub = types.ModuleType("common.constants")
    constants_stub.CHROMA_COLLECTIONS = {
        "conversion_rules": SimpleNamespace(domain="documents", description="", prompt_type="documental"),
        "troubleshooting": SimpleNamespace(domain="code", description="", prompt_type="documental"),
        "multimedia_assets": SimpleNamespace(domain="multimedia", description="", prompt_type="multimedia"),
        "legal_repository": SimpleNamespace(domain="legal", description="", prompt_type="legal"),
    }

    class _StubCollection:
        def __init__(self, name: str) -> None:
            self._name = name

        def count(self) -> int:
            return 0

    class _StubSettings:
        def get_collection(self, name: str) -> _StubCollection:
            return _StubCollection(name)

    constants_stub.CHROMA_SETTINGS = _StubSettings()
    monkeypatch.setitem(sys.modules, "common.constants", constants_stub)
    monkeypatch.setattr(common_pkg, "constants", constants_stub, raising=False)

    chroma_stub = types.ModuleType("common.chroma_db_settings")

    class _PlaceholderChroma:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    chroma_stub.Chroma = _PlaceholderChroma
    monkeypatch.setitem(sys.modules, "common.chroma_db_settings", chroma_stub)
    monkeypatch.setattr(common_pkg, "chroma_db_settings", chroma_stub, raising=False)

    translations_stub = types.ModuleType("common.translations")
    translations_stub.get_text = lambda key, lang="es", **_: f"{lang}:{key}"
    monkeypatch.setitem(sys.modules, "common.translations", translations_stub)
    monkeypatch.setattr(common_pkg, "translations", translations_stub, raising=False)

    assistant_stub = types.ModuleType("common.assistant_prompt")
    assistant_stub.assistant_prompt = lambda language="es": language
    monkeypatch.setitem(sys.modules, "common.assistant_prompt", assistant_stub)
    monkeypatch.setattr(common_pkg, "assistant_prompt", assistant_stub, raising=False)

    observability_stub = types.ModuleType("common.observability")
    observability_stub.record_rag_response = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "common.observability", observability_stub)
    monkeypatch.setattr(common_pkg, "observability", observability_stub, raising=False)

    text_norm_module = importlib.import_module("app.common.text_normalization")
    monkeypatch.setitem(sys.modules, "common.text_normalization", text_norm_module)
    monkeypatch.setattr(common_pkg, "text_normalization", text_norm_module, raising=False)

    monkeypatch.delitem(sys.modules, "app.common.langchain_module", raising=False)
    module = importlib.import_module("app.common.langchain_module")

    harness = _Harness()

    def fake_get_text(key: str, language: str, **_: object) -> str:
        return f"{language}:{key}"

    monkeypatch.setattr(module, "get_text", fake_get_text)
    monkeypatch.setattr(
        module,
        "parse_arguments",
        lambda: SimpleNamespace(hide_source=False, mute_stream=True),
    )
    monkeypatch.setattr(module, "HuggingFaceEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(module, "StreamingStdOutCallbackHandler", FakeStreamingHandler)
    monkeypatch.setattr(module, "RunnableLambda", lambda func: FakeRunnable(func))
    monkeypatch.setattr(module, "RunnablePassthrough", lambda: FakeRunnable(lambda value: value))
    monkeypatch.setattr(module, "StrOutputParser", lambda: FakeParser())
    monkeypatch.setattr(module, "Ollama", lambda *args, **kwargs: FakeLLM(harness.run_llm))
    monkeypatch.setattr(module, "record_rag_response", harness.record_metrics)
    monkeypatch.setattr(module, "PROMPT_BUILDERS", build_prompt_builders(harness.record_prompt), raising=False)

    class _FakeCollection:
        def __init__(self, name: str) -> None:
            self._name = name

        def count(self) -> int:
            return harness.document_count(self._name)

    fake_client = SimpleNamespace(get_collection=lambda name: _FakeCollection(name))
    monkeypatch.setattr(module, "CHROMA_SETTINGS", fake_client)

    class _FakeChroma:
        def __init__(self, *_, collection_name: str | None = None, **__):
            self.collection_name = collection_name or "vectordb"

        def as_retriever(self, **kwargs):
            harness.retriever_kwargs = kwargs
            retriever = FakeRetriever(self.collection_name, harness.docs_for(self.collection_name))
            harness.retrievers.append(retriever)
            return retriever

    monkeypatch.setattr(module, "Chroma", _FakeChroma)

    module._collections_cache.clear()
    module._embeddings_instance = None

    return module, harness


@pytest.mark.parametrize(
    ("description", "query", "language", "expected_response"),
    [
        (
            "pregunta corta en español",
            "¿Qué es RAG y por qué es útil?",
            "es",
            "Respuesta breve en español con los puntos esenciales.",
        ),
        (
            "pregunta larga en inglés",
            (
                "Please provide a detailed summary of the roadmap objectives, key metrics, "
                "and the milestones that were prioritised during the last quarterly review."
            ),
            "en",
            "Detailed answer in English covering objectives, metrics, and milestones.",
        ),
        (
            "pregunta con acentos",
            "¿Cómo impacta la acción preventiva en la auditoría de calidad?",
            "es",
            "La acción preventiva mantiene la auditoría en conformidad y evita reprocesos.",
        ),
    ],
)
def test_response_regressions(description, query, language, expected_response, rag_test_harness):
    """Validate that ``response`` returns deterministic outputs for representative prompts."""

    module, harness = rag_test_harness
    harness.set_docs(
        "Contexto relevante con métricas trimestrales y hallazgos.",
        "La acción preventiva es crítica para evitar desviaciones recurrentes.",
    )

    normalised_query = normalize_to_nfc(query).strip()

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == language
        assert payload["question"] == normalised_query
        assert isinstance(payload["context"], str)
        assert payload["context"], "El contexto formateado no debe estar vacío."
        if "acentos" in description:
            assert "acción" in payload["question"]
            assert "acción" in payload["context"]
        return expected_response

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    result = module.response(query, language=language)

    assert result == expected_response
    assert harness.prompt_inputs, "Se esperaba al menos una invocación al prompt."
    assert harness.retriever_kwargs == {"search_kwargs": {"k": module.target_source_chunks}}

    last_invocation = harness.llm_invocations[-1]
    assert last_invocation["language"] == language
    assert last_invocation["question"] == normalised_query

    if "acentos" in description:
        assert "acción" in result
        assert "accion" not in result, "La respuesta debe mantener los acentos esperados."

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["language"] == language
    assert event["status"] == "success"
    documents = event["kwargs"].get("collection_documents")
    assert set(documents.keys()) == {"conversion_rules", "troubleshooting"}
    for collection_name in ("conversion_rules", "troubleshooting"):
        assert documents[collection_name] == len(harness.docs_for(collection_name))


def test_response_uses_task_metadata_for_collection_selection(rag_test_harness):
    """Metadata should restrict retrieval to the requested collection and variant."""

    module, harness = rag_test_harness
    harness.set_docs_for("legal_repository", "Cláusulas actualizadas para el contrato marco.")
    harness.set_docs("Contexto general sin priorización.")

    expected = "Respuesta legal detallada."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "legal"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    metadata = {"collections": ["legal_repository"], "prompt_type": "legal"}
    result = module.response(
        "¿Cuál es la obligación contractual vigente?",
        language="es",
        task_type="legal_query",
        metadata=metadata,
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "legal"
    assert {retriever.collection_name for retriever in harness.retrievers} == {"legal_repository"}
    assert harness.selected_collections == ["legal_repository"]

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["kwargs"].get("collection_documents") == {"legal_repository": len(harness.docs_for("legal_repository"))}


def test_response_uses_task_type_hints_for_multimedia(rag_test_harness):
    """Tasks with multimedia hints should pivot to the multimedia prompt and collection."""

    module, harness = rag_test_harness
    harness.set_docs_for("multimedia_assets", "Transcripción del video de lanzamiento.")

    expected = "Resumen multimedia generado."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "multimedia"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    result = module.response(
        "Necesito un resumen del último video corporativo",
        language="es",
        task_type="media_summary",
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "multimedia"
    assert {retriever.collection_name for retriever in harness.retrievers} == {"multimedia_assets"}
    assert harness.selected_collections == ["multimedia_assets"]

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["kwargs"].get("collection_documents") == {"multimedia_assets": len(harness.docs_for("multimedia_assets"))}


def test_response_falls_back_when_selected_collection_is_empty(rag_test_harness):
    """If the requested collection has no documents the pipeline should fallback."""

    module, harness = rag_test_harness
    harness.set_docs("Contexto general consolidado.")
    harness.set_docs_for("multimedia_assets")  # sin documentos disponibles

    expected = "Respuesta documental alternativa."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "documental"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    result = module.response(
        "Comparte los lineamientos vigentes",
        language="es",
        task_type="document_query",
        metadata={"collections": ["multimedia_assets"]},
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "documental"
    assert {
        retriever.collection_name for retriever in harness.retrievers
    } == {"conversion_rules", "troubleshooting", "legal_repository"}
    assert set(harness.selected_collections) == {
        "conversion_rules",
        "troubleshooting",
        "legal_repository",
    }

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    documents = event["kwargs"].get("collection_documents")
    assert set(documents.keys()) == {
        "conversion_rules",
        "troubleshooting",
        "legal_repository",
    }
    for collection_name in documents:
        assert documents[collection_name] == len(harness.docs_for(collection_name))

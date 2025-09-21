"""Regression tests for the RAG response flow."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, List

import pytest

from app.common.text_normalization import normalize_to_nfc


class _FakeDoc:
    """Simple container that mimics a Chroma document."""

    def __init__(self, page_content: str) -> None:
        self.page_content = page_content


class _Harness:
    """Configurable harness that captures the behaviour of the RAG pipeline."""

    def __init__(self) -> None:
        self.llm_callback: Callable[[dict], str] | None = None
        self._docs: List[_FakeDoc] = [_FakeDoc("Contexto simulado.")]
        self.prompt_inputs: list[dict] = []
        self.llm_invocations: list[dict] = []
        self.retriever_kwargs: dict | None = None
        self.doc_count: int = 1

    def set_docs(self, *contents: str) -> None:
        """Configure the documents returned by the fake retriever."""

        if contents:
            self._docs = [_FakeDoc(text) for text in contents]
            self.doc_count = len(self._docs)
        else:
            self._docs = []
            self.doc_count = 0

    def docs_callback(self, _query: str) -> List[_FakeDoc]:
        """Return the fake documents for a given query."""

        return self._docs

    def set_llm_callback(self, callback: Callable[[dict], str]) -> None:
        """Define the LLM callback used by the fake Ollama client."""

        self.llm_callback = callback


@pytest.fixture
def rag_test_harness(monkeypatch):
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

    chroma_stub = types.ModuleType("common.chroma_db_settings")

    class _PlaceholderChroma:
        def __init__(self, *args, **kwargs) -> None:
            pass

    chroma_stub.Chroma = _PlaceholderChroma
    monkeypatch.setitem(sys.modules, "common.chroma_db_settings", chroma_stub)
    monkeypatch.setattr(common_pkg, "chroma_db_settings", chroma_stub, raising=False)

    constants_stub = types.ModuleType("common.constants")

    class _PlaceholderCollection:
        def count(self) -> int:
            return 0

    class _PlaceholderSettings:
        def get_collection(self, _name: str) -> _PlaceholderCollection:
            return _PlaceholderCollection()

    constants_stub.CHROMA_SETTINGS = _PlaceholderSettings()
    monkeypatch.setitem(sys.modules, "common.constants", constants_stub)
    monkeypatch.setattr(common_pkg, "constants", constants_stub, raising=False)

    assistant_stub = types.ModuleType("common.assistant_prompt")

    def _placeholder_prompt(language: str = "es"):
        return language

    assistant_stub.assistant_prompt = _placeholder_prompt
    monkeypatch.setitem(sys.modules, "common.assistant_prompt", assistant_stub)
    monkeypatch.setattr(common_pkg, "assistant_prompt", assistant_stub, raising=False)

    translations_stub = types.ModuleType("common.translations")

    def _placeholder_get_text(key: str, lang: str = "es", **_: object) -> str:
        return f"{lang}:{key}"

    translations_stub.get_text = _placeholder_get_text
    monkeypatch.setitem(sys.modules, "common.translations", translations_stub)
    monkeypatch.setattr(common_pkg, "translations", translations_stub, raising=False)

    text_norm_module = importlib.import_module("app.common.text_normalization")
    monkeypatch.setitem(sys.modules, "common.text_normalization", text_norm_module)
    monkeypatch.setattr(common_pkg, "text_normalization", text_norm_module, raising=False)

    monkeypatch.delitem(sys.modules, "app.common.langchain_module", raising=False)
    module = importlib.import_module("app.common.langchain_module")

    harness = _Harness()

    class _FakeRunnable:
        def __init__(self, func: Callable[[str], object]) -> None:
            self._func = func

        def invoke(self, value: str) -> object:
            return self._func(value)

        def __or__(self, other):  # type: ignore[override]
            if hasattr(other, "invoke"):
                return _FakeRunnable(lambda x: other.invoke(self.invoke(x)))
            if callable(other):
                return _FakeRunnable(lambda x: other(self.invoke(x)))
            raise TypeError(f"Unsupported pipe target: {other!r}")

    class _FakeRetriever(_FakeRunnable):
        def __init__(self) -> None:
            super().__init__(lambda query: harness.docs_callback(query))

    class _FakeChroma:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature parity
            pass

        def as_retriever(self, **kwargs):
            harness.retriever_kwargs = kwargs
            return _FakeRetriever()

    class _FakePrompt:
        def __init__(self, language: str) -> None:
            self.language = language

        def __ror__(self, other):  # type: ignore[override]
            context_runnable = other["context"]
            question_runnable = other["question"]

            def _run(value: str) -> dict:
                payload = {
                    "context": context_runnable.invoke(value),
                    "question": question_runnable.invoke(value),
                    "language": self.language,
                }
                harness.prompt_inputs.append(payload)
                return payload

            return _FakeRunnable(_run)

    class _FakeLLM:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature parity
            pass

        def invoke(self, payload: dict) -> str:
            harness.llm_invocations.append(payload)
            if harness.llm_callback is None:
                raise AssertionError("LLM callback was not configured for the test case.")
            return harness.llm_callback(payload)

    class _FakeParser:
        def invoke(self, value: str) -> str:
            return value

    class _FakeStreamingHandler:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature parity
            pass

    class _FakeEmbeddings:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature parity
            pass

    class _FakeCollection:
        def count(self) -> int:
            return harness.doc_count

    class _FakeChromaSettings:
        def get_collection(self, _name: str) -> _FakeCollection:
            return _FakeCollection()

    def _fake_assistant_prompt(language: str) -> _FakePrompt:
        return _FakePrompt(language)

    def _fake_runnable_passthrough() -> _FakeRunnable:
        return _FakeRunnable(lambda value: value)

    monkeypatch.setattr(module, "HuggingFaceEmbeddings", _FakeEmbeddings)
    monkeypatch.setattr(module, "Chroma", _FakeChroma)
    monkeypatch.setattr(module, "assistant_prompt", _fake_assistant_prompt)
    monkeypatch.setattr(module, "StreamingStdOutCallbackHandler", _FakeStreamingHandler)
    monkeypatch.setattr(module, "Ollama", _FakeLLM)
    monkeypatch.setattr(module, "StrOutputParser", lambda: _FakeParser())
    monkeypatch.setattr(module, "RunnablePassthrough", _fake_runnable_passthrough)
    monkeypatch.setattr(module, "parse_arguments", lambda: SimpleNamespace(mute_stream=True))
    monkeypatch.setattr(module, "CHROMA_SETTINGS", _FakeChromaSettings())

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

    result = module.response(query, language=language)

    assert result == expected_response
    assert harness.prompt_inputs, "Se esperaba al menos una invocación al prompt."
    assert harness.retriever_kwargs == {"search_kwargs": {"k": module.target_source_chunks}}

    last_invocation = harness.llm_invocations[-1]
    assert last_invocation["language"] == language
    assert last_invocation["question"] == normalised_query

    if "acentos" in description:
        assert "acción" in result

    # Confirm that the accent-sensitive checks would fail if accents were missing.
    if "acentos" in description:
        assert "accion" not in result, "La respuesta debe mantener los acentos esperados."

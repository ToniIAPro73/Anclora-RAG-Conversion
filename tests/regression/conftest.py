from __future__ import annotations

import importlib
import sys
import types
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, List

import pytest


class _FakeDoc:
    """Simple container that mimics a Chroma document."""

    def __init__(self, page_content: str, collection: str = "conversion_rules") -> None:
        self.page_content = page_content
        self.metadata = {"collection": collection}


class _Harness:
    """Configurable harness that captures the behaviour of the RAG pipeline."""

    def __init__(self) -> None:
        self.llm_callback: Callable[[dict], str] | None = None
        self._docs: List[_FakeDoc] = [_FakeDoc("Contexto simulado.")]
        self.prompt_inputs: list[dict] = []
        self.llm_invocations: list[dict] = []
        self.retriever_kwargs: dict | None = None
        self.doc_count: int = 1
        self.collection_sizes: dict[str, int] = {"conversion_rules": 1}
        self.collection_domains: dict[str, str] = {}
        self.context_breakdown: dict[str, int] = {}
        self.last_metrics: dict[str, object] = {}

    def set_docs(self, *contents: str | tuple[str, str]) -> None:
        """Configure the documents returned by the fake retriever."""

        if contents:
            docs: List[_FakeDoc] = []
            for entry in contents:
                if isinstance(entry, tuple):
                    text, collection = entry
                else:
                    text, collection = entry, "conversion_rules"
                docs.append(_FakeDoc(str(text), str(collection)))
            self._docs = docs
            breakdown = Counter(doc.metadata.get("collection", "conversion_rules") for doc in docs)
            self.collection_sizes = dict(breakdown)
            self.doc_count = len(self._docs)
        else:
            self._docs = []
            self.doc_count = 0
            self.collection_sizes = {}

        if self.collection_domains:
            for name in self.collection_domains:
                self.collection_sizes.setdefault(name, 0)

        self.context_breakdown = {}
        self.last_metrics = {}

    def docs_callback(self, _query: str, collection: str | None = None) -> List[_FakeDoc]:
        """Return the fake documents for a given query, optionally filtered."""

        if collection is None:
            return list(self._docs)

        filtered = [
            doc
            for doc in self._docs
            if doc.metadata.get("collection", "conversion_rules") == collection
        ]
        return filtered

    def set_llm_callback(self, callback: Callable[[dict], str]) -> None:
        """Define the LLM callback used by the fake Ollama client."""

        self.llm_callback = callback

    def capture_metrics(self, *args, **kwargs) -> None:
        """Store the last metrics payload recorded during the test."""

        self.last_metrics = {"args": args, "kwargs": kwargs}
        context_info = kwargs.get("context_collections")
        if isinstance(context_info, dict):
            self.context_breakdown = dict(context_info)


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
    created_modules = list(stubbed_modules)

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

    observability_module = importlib.import_module("app.common.observability")
    monkeypatch.setitem(sys.modules, "common.observability", observability_module)
    monkeypatch.setattr(common_pkg, "observability", observability_module, raising=False)

    chroma_stub = types.ModuleType("common.chroma_db_settings")

    class _PlaceholderChroma:
        def __init__(self, *args, **kwargs) -> None:
            pass

    chroma_stub.Chroma = _PlaceholderChroma
    monkeypatch.setitem(sys.modules, "common.chroma_db_settings", chroma_stub)
    monkeypatch.setattr(common_pkg, "chroma_db_settings", chroma_stub, raising=False)

    created_modules.append("common.chroma_db_settings")

    constants_stub = types.ModuleType("common.constants")

    class _PlaceholderCollection:
        def count(self) -> int:
            return 0

    class _PlaceholderSettings:
        def get_collection(self, _name: str) -> _PlaceholderCollection:
            return _PlaceholderCollection()

    constants_stub.CHROMA_SETTINGS = _PlaceholderSettings()
    constants_stub.CHROMA_COLLECTIONS = {
        "conversion_rules": SimpleNamespace(domain="documents"),
        "troubleshooting": SimpleNamespace(domain="code"),
        "multimedia_assets": SimpleNamespace(domain="multimedia"),
    }
    constants_stub.DOMAIN_TO_COLLECTION = {
        config.domain: name for name, config in constants_stub.CHROMA_COLLECTIONS.items()
    }
    monkeypatch.setitem(sys.modules, "common.constants", constants_stub)
    monkeypatch.setattr(common_pkg, "constants", constants_stub, raising=False)

    created_modules.append("common.constants")

    assistant_stub = types.ModuleType("common.assistant_prompt")

    def _placeholder_prompt(language: str = "es"):
        return language

    assistant_stub.assistant_prompt = _placeholder_prompt
    monkeypatch.setitem(sys.modules, "common.assistant_prompt", assistant_stub)
    monkeypatch.setattr(common_pkg, "assistant_prompt", assistant_stub, raising=False)

    created_modules.append("common.assistant_prompt")

    translations_stub = types.ModuleType("common.translations")

    def _placeholder_get_text(key: str, lang: str = "es", **_: object) -> str:
        return f"{lang}:{key}"

    translations_stub.get_text = _placeholder_get_text
    monkeypatch.setitem(sys.modules, "common.translations", translations_stub)
    monkeypatch.setattr(common_pkg, "translations", translations_stub, raising=False)

    created_modules.append("common.translations")

    text_norm_module = importlib.import_module("app.common.text_normalization")
    monkeypatch.setitem(sys.modules, "common.text_normalization", text_norm_module)
    monkeypatch.setattr(common_pkg, "text_normalization", text_norm_module, raising=False)

    created_modules.append("common.text_normalization")

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
        def __init__(self, collection: str | None) -> None:
            super().__init__(lambda query: harness.docs_callback(query, collection))
            self._collection = collection

        def get_relevant_documents(self, query: str):
            return harness.docs_callback(query, self._collection)

    class _FakeChroma:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature parity
            self._collection = kwargs.get("collection_name")

        def as_retriever(self, **kwargs):
            harness.retriever_kwargs = kwargs
            return _FakeRetriever(self._collection)

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
        def __init__(self, name: str) -> None:
            self._name = name

        def count(self) -> int:
            return harness.collection_sizes.get(self._name, 0)

    class _FakeChromaSettings:
        def get_collection(self, name: str) -> _FakeCollection:
            return _FakeCollection(name)

    def _fake_assistant_prompt(language: str) -> _FakePrompt:
        return _FakePrompt(language)

    def _fake_runnable_passthrough() -> _FakeRunnable:
        return _FakeRunnable(lambda value: value)

    harness.collection_domains = {
        name: config.domain for name, config in module.CHROMA_COLLECTIONS.items()
    }
    for name in harness.collection_domains:
        harness.collection_sizes.setdefault(name, 0)

    original_record = module.record_rag_response

    def _capture_metrics(*args, **kwargs):
        harness.capture_metrics(*args, **kwargs)
        return original_record(*args, **kwargs)

    monkeypatch.setattr(module, "record_rag_response", _capture_metrics)
    monkeypatch.setattr(module, "HuggingFaceEmbeddings", _FakeEmbeddings)
    monkeypatch.setattr(module, "Chroma", _FakeChroma)
    monkeypatch.setattr(module, "assistant_prompt", _fake_assistant_prompt)
    monkeypatch.setattr(module, "StreamingStdOutCallbackHandler", _FakeStreamingHandler)
    monkeypatch.setattr(module, "Ollama", _FakeLLM)
    monkeypatch.setattr(module, "StrOutputParser", lambda: _FakeParser())
    monkeypatch.setattr(module, "RunnablePassthrough", _fake_runnable_passthrough)
    monkeypatch.setattr(module, "parse_arguments", lambda: SimpleNamespace(mute_stream=True))
    monkeypatch.setattr(module, "CHROMA_SETTINGS", _FakeChromaSettings())

    def _fast_detect_language(text: str) -> str:
        normalized_text = module.normalize_to_nfc(text or "")
        stripped_text = normalized_text.strip()
        if not stripped_text:
            return "es"

        normalized_lower = stripped_text.lower()
        tokens = {
            token
            for token in module.re.split(r"\W+", normalized_lower)
            if token
        }

        if any(char in module.SPANISH_HINT_CHARACTERS for char in stripped_text):
            return "es"
        if any(word in normalized_lower for word in module.SPANISH_HINT_WORDS):
            return "es"
        if tokens & module.ENGLISH_HINT_WORDS:
            return "en"
        if stripped_text.isascii():
            return "en"
        return "es"

    monkeypatch.setattr(module, "detect_language", _fast_detect_language)

    document_agent_module = sys.modules.get("app.agents.document_agent.agent")
    if document_agent_module is not None:
        monkeypatch.setattr(document_agent_module, "langchain_module", module, raising=False)

    try:
        yield module, harness
    finally:
        for name in created_modules:
            sys.modules.pop(name, None)

        sys.modules.pop("app.common.langchain_module", None)


__all__ = ["rag_test_harness", "_Harness", "_FakeDoc"]

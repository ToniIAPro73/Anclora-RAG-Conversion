"""Utility mocks used across RAG tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class FakeDoc:
    """Simple container that mimics a Chroma document."""

    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "FakeDoc":
        return FakeDoc(self.page_content, dict(self.metadata))


class FakeRunnable:
    """Lightweight runnable compatible with LangChain style piping."""

    def __init__(self, func: Callable[[Any], Any]) -> None:
        self._func = func

    def invoke(self, value: Any) -> Any:
        return self._func(value)

    def __call__(self, value: Any) -> Any:  # pragma: no cover - parity helper
        return self._func(value)

    def __or__(self, other: Any) -> "FakeRunnable":  # pragma: no cover - piping helper
        if hasattr(other, "invoke"):
            return FakeRunnable(lambda value: other.invoke(self.invoke(value)))
        if callable(other):
            return FakeRunnable(lambda value: other(self.invoke(value)))
        raise TypeError(f"Unsupported pipe target: {other!r}")

    def __ror__(self, other: Any) -> "FakeRunnable":  # pragma: no cover - piping helper
        if hasattr(other, "invoke"):
            return FakeRunnable(lambda value: self.invoke(other.invoke(value)))
        if callable(other):
            return FakeRunnable(lambda value: self.invoke(other(value)))
        raise TypeError(f"Unsupported pipe source: {other!r}")


class FakeRetriever(FakeRunnable):
    """Retriever that records queries and returns cloned documents."""

    def __init__(
        self,
        collection_name: str,
        documents: List[FakeDoc],
        on_query: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.collection_name = collection_name
        self._documents = list(documents)
        self.queries: List[str] = []
        self._on_query = on_query

        def _run(query: str) -> List[FakeDoc]:
            self.queries.append(query)
            if self._on_query is not None:
                self._on_query(query)
            return [doc.clone() for doc in self._documents]

        super().__init__(_run)


class FakePrompt:
    """Prompt template stub that records invocations."""

    def __init__(
        self,
        language: str,
        variant: Optional[str] = None,
        recorder: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.language = language
        self.variant = variant
        self.invocations: List[Dict[str, Any]] = []
        self._recorder = recorder

    def __ror__(self, mapping: Dict[str, FakeRunnable]) -> FakeRunnable:
        context_runnable = mapping["context"]
        question_runnable = mapping["question"]

        def _run(value: str) -> Dict[str, Any]:
            payload = {
                "context": context_runnable.invoke(value),
                "question": question_runnable.invoke(value),
                "language": self.language,
                "prompt_variant": self.variant,
            }
            self.invocations.append(payload)
            if self._recorder is not None:
                self._recorder(payload)
            return payload

        return FakeRunnable(_run)


class FakeLLM:
    """Fake LLM that uses a callback to produce deterministic outputs."""

    def __init__(self, callback: Callable[[Dict[str, Any]], str]) -> None:
        self._callback = callback
        self.invocations: List[Dict[str, Any]] = []

    def invoke(self, payload: Dict[str, Any]) -> str:
        self.invocations.append(payload)
        if self._callback is None:  # pragma: no cover - defensive guard
            raise AssertionError("LLM callback was not configured.")
        return self._callback(payload)

    def __ror__(self, previous: FakeRunnable) -> FakeRunnable:  # pragma: no cover - piping helper
        return FakeRunnable(lambda value: self.invoke(previous.invoke(value)))


class FakeParser:
    """Passthrough output parser used in regression tests."""

    def invoke(self, value: str) -> str:  # pragma: no cover - trivial
        return value

    def __ror__(self, previous: FakeRunnable) -> FakeRunnable:  # pragma: no cover - piping helper
        return FakeRunnable(lambda value: previous.invoke(value))


class FakeStreamingHandler:
    """Placeholder for the streaming callback used by the pipeline."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - parity helper
        pass


class FakeEmbeddings:
    """Minimal embeddings stub accepted by the RAG pipeline."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - parity helper
        pass


def build_prompt_builders(
    recorder: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Callable[[str], FakePrompt]]:
    """Create prompt builder mapping suitable for monkeypatching the module."""

    def _factory(language: str, variant: Optional[str]) -> FakePrompt:
        return FakePrompt(language=language, variant=variant, recorder=recorder)

    return {
        "documental": lambda language: _factory(language, "documental"),
        "multimedia": lambda language: _factory(language, "multimedia"),
        "legal": lambda language: _factory(language, "legal"),
    }


__all__ = [
    "FakeDoc",
    "FakeEmbeddings",
    "FakeLLM",
    "FakeParser",
    "FakePrompt",
    "FakeRetriever",
    "FakeRunnable",
    "FakeStreamingHandler",
    "build_prompt_builders",
]

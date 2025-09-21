"""Test configuration helpers."""

import sys
import types
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    """Add the repository root to ``sys.path`` for module resolution."""

    project_root = Path(__file__).resolve().parent.parent
    root_as_str = str(project_root)
    if root_as_str not in sys.path:
        sys.path.insert(0, root_as_str)


def _ensure_app_dir_on_path() -> None:
    """Expose the ``app`` package as a namespace package for imports."""

    app_dir = Path(__file__).resolve().parent.parent / "app"
    app_dir_str = str(app_dir)
    if app_dir.is_dir() and app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)


def _install_stub_submodule(fullname: str, **attributes: object) -> None:
    """Register a lightweight stub module under ``fullname`` if needed."""

    if fullname in sys.modules:
        return

    module = types.ModuleType(fullname)
    for attr_name, attr_value in attributes.items():
        setattr(module, attr_name, attr_value)
    sys.modules[fullname] = module

    parent_name, _, child_name = fullname.rpartition(".")
    if parent_name:
        parent = sys.modules.get(parent_name)
        if parent is None:
            parent = types.ModuleType(parent_name)
            sys.modules[parent_name] = parent
        setattr(parent, child_name, module)


def _install_langchain_stubs() -> None:
    """Provide minimal stand-ins for optional langchain dependencies."""

    try:  # pragma: no cover - only exercised when dependency is missing
        import langchain  # type: ignore  # noqa: F401
        import langchain_community  # type: ignore  # noqa: F401
        import langchain_core  # type: ignore  # noqa: F401
        import langchain.callbacks.streaming_stdout  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover - stub path
        _install_stub_submodule("langchain.chains", RetrievalQA=type("RetrievalQA", (), {}))

        class _HuggingFaceEmbeddings:
            def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
                """Placeholder constructor."""

        class _Ollama:
            def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
                """Placeholder constructor."""

        _install_stub_submodule(
            "langchain_community.embeddings",
            HuggingFaceEmbeddings=_HuggingFaceEmbeddings,
        )
        _install_stub_submodule(
            "langchain_community.llms",
            Ollama=_Ollama,
        )

        class _StreamingStdOutCallbackHandler:
            def __call__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
                """Placeholder callable."""

        _install_stub_submodule(
            "langchain.callbacks.streaming_stdout",
            StreamingStdOutCallbackHandler=_StreamingStdOutCallbackHandler,
        )

        class _StrOutputParser:
            def __call__(self, value: object) -> object:
                return value

        class _RunnablePassthrough:
            def __call__(self, value: object) -> object:
                return value

        class _ChatPromptTemplate:
            def __init__(self, messages: tuple[str, object]) -> None:
                self.messages = messages

            @classmethod
            def from_messages(cls, messages: tuple[str, object]) -> "_ChatPromptTemplate":
                return cls(messages)

        _install_stub_submodule(
            "langchain_core.output_parsers",
            StrOutputParser=_StrOutputParser,
        )
        _install_stub_submodule(
            "langchain_core.runnables",
            RunnablePassthrough=_RunnablePassthrough,
        )
        _install_stub_submodule(
            "langchain_core.prompts",
            ChatPromptTemplate=_ChatPromptTemplate,
        )


def _install_common_stubs() -> None:
    """Provide lightweight fallbacks for optional ``common`` modules."""

    try:  # pragma: no cover - prefer real modules when available
        import common.constants  # type: ignore  # noqa: F401
        import common.chroma_db_settings  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover - stub path
        class _StubCollection:
            def count(self) -> int:
                return 1

        class _StubChromaSettings:
            def get_collection(self, name: str) -> _StubCollection:
                return _StubCollection()

        _install_stub_submodule(
            "common.constants",
            CHROMA_SETTINGS=_StubChromaSettings(),
        )

        class _StubRetriever:
            def __ror__(self, other: object) -> object:
                return other

        class _StubChroma:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def as_retriever(self, *args: object, **kwargs: object) -> _StubRetriever:
                return _StubRetriever()

        _install_stub_submodule(
            "common.chroma_db_settings",
            Chroma=_StubChroma,
        )


_ensure_project_root_on_path()
_ensure_app_dir_on_path()
_install_langchain_stubs()
_install_common_stubs()

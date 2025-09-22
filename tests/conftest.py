"""Test configuration helpers."""

import sys
import types
import typing
from pathlib import Path


def _patch_forward_ref_evaluate() -> None:
    """Adapt ``typing.ForwardRef._evaluate`` for Python 3.12 + Pydantic v1."""

    if sys.version_info < (3, 12):  # pragma: no cover - legacy behavior
        return

    original_evaluate = typing.ForwardRef._evaluate

    def _evaluate(self, globalns, localns, *args, **kwargs):  # type: ignore[override]
        type_params = kwargs.pop("type_params", None)
        recursive_guard = kwargs.pop("recursive_guard", None)

        remaining_args = list(args)
        if type_params is None and remaining_args:
            candidate = remaining_args.pop(0)
            if isinstance(candidate, (set, frozenset)):
                recursive_guard = candidate
            else:
                type_params = candidate

        if recursive_guard is None and remaining_args:
            recursive_guard = remaining_args.pop(0)

        if recursive_guard is None:
            recursive_guard = set()

        return original_evaluate(
            self,
            globalns,
            localns,
            type_params,
            recursive_guard=recursive_guard,
        )

    typing.ForwardRef._evaluate = _evaluate  # type: ignore[assignment]


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

    def _install_stubbed_dependencies() -> None:
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

        _install_stub_submodule(
            "langchain_core.documents",
            Document=type("Document", (), {}),
        )
        _install_stub_submodule(
            "langchain_core.embeddings",
            Embeddings=type("Embeddings", (), {}),
        )
        _install_stub_submodule(
            "langchain_core.vectorstores",
            VectorStore=type("VectorStore", (), {}),
        )

        def _xor_args(*_args, **_kwargs):  # type: ignore[override]
            def _decorator(func):
                return func

            return _decorator

        _install_stub_submodule("langchain_core.utils", xor_args=_xor_args)

        def _maximal_marginal_relevance(*_args, **_kwargs):  # type: ignore[override]
            return []

        _install_stub_submodule(
            "langchain_community.vectorstores.utils",
            maximal_marginal_relevance=_maximal_marginal_relevance,
        )

        class _StrOutputParser:
            def __call__(self, value: object) -> object:
                return value

        class _RunnablePassthrough:
            def __call__(self, value: object) -> object:
                return value

        class _RunnableLambda:
            def __init__(self, func):
                self._func = func

            def __call__(self, value: object) -> object:
                return func(value) if callable(func := self._func) else value

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
            RunnableLambda=_RunnableLambda,
        )
        _install_stub_submodule(
            "langchain_core.prompts",
            ChatPromptTemplate=_ChatPromptTemplate,
        )

    _install_stubbed_dependencies()


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

    if "common.ingest_file" not in sys.modules:
        def _validate_uploaded_file(uploaded_file) -> tuple[bool, str]:  # type: ignore[override]
            return True, "Válido"

        def _ingest_file(*args: object, **kwargs: object) -> None:
            return None

        def _delete_file_from_vectordb(filename: str) -> None:
            return None

        _install_stub_submodule(
            "common.ingest_file",
            ingest_file=_ingest_file,
            validate_uploaded_file=_validate_uploaded_file,
            delete_file_from_vectordb=_delete_file_from_vectordb,
        )


def _install_langdetect_stub() -> None:
    """Install a minimal stub for ``langdetect`` when the dependency is absent."""

    try:  # pragma: no cover - prefer the actual dependency when available
        import langdetect  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover - stub path
        class _DetectorFactory:
            seed = 0

        class _LangDetectException(Exception):
            pass

        def _detect(text: str) -> str:
            return "es" if text else ""

        _install_stub_submodule(
            "langdetect",
            DetectorFactory=_DetectorFactory,
            LangDetectException=_LangDetectException,
            detect=_detect,
        )


_patch_forward_ref_evaluate()
_ensure_project_root_on_path()
_ensure_app_dir_on_path()
_install_langchain_stubs()
_install_common_stubs()
_install_langdetect_stub()

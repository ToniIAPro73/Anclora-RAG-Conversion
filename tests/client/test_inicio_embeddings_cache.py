"""Tests for the Streamlit home page module."""

from __future__ import annotations

import importlib
import sys
import types


def _install_streamlit_stub(monkeypatch) -> None:
    """Register a lightweight ``streamlit`` stub for module imports."""

    class _SessionState(dict):
        def __getattr__(self, name: str):  # noqa: D401 - simple proxy
            try:
                return self[name]
            except KeyError as exc:  # pragma: no cover - defensive branch
                raise AttributeError(name) from exc

        def __setattr__(self, name: str, value) -> None:  # noqa: D401 - simple proxy
            self[name] = value

    class _Sidebar:
        def __enter__(self) -> "_Sidebar":  # noqa: D401 - context protocol
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: D401 - context protocol
            return False

        def title(self, *args, **kwargs) -> None:  # noqa: D401 - optional API compatibility
            return None

        def header(self, *args, **kwargs) -> None:  # noqa: D401 - optional API compatibility
            return None

        def caption(self, *args, **kwargs) -> None:  # noqa: D401 - optional API compatibility
            return None

        def selectbox(self, *args, **kwargs):  # noqa: D401 - optional API compatibility
            return _selectbox(*args, **kwargs)

    class _ChatMessage:
        def __init__(self, role: str) -> None:
            self.role = role

        def __enter__(self) -> "_ChatMessage":  # noqa: D401 - context protocol
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: D401 - context protocol
            return False

        def markdown(self, *args, **kwargs) -> None:  # noqa: D401 - mimic Streamlit API
            return None

    class _Spinner:
        def __init__(self, message: object) -> None:
            self.message = message

        def __enter__(self) -> "_Spinner":  # noqa: D401 - context protocol
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: D401 - context protocol
            return False

    def _selectbox(label, options, format_func=lambda value: value, index=0, help=None, key=None):

        del label, format_func, help
        _ = key
        if not options:
            return None
        if not isinstance(index, int) or index < 0 or index >= len(options):
            index = 0
        return options[index]

    streamlit_module = types.ModuleType("streamlit")
    streamlit_module.session_state = _SessionState()  # type: ignore[attr-defined]
    streamlit_module.set_page_config = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.sidebar = _Sidebar()  # type: ignore[attr-defined]
    streamlit_module.header = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.title = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.caption = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.markdown = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.selectbox = _selectbox  # type: ignore[attr-defined]
    streamlit_module.chat_message = lambda role: _ChatMessage(str(role))  # type: ignore[attr-defined]
    streamlit_module.chat_input = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.spinner = lambda message: _Spinner(message)  # type: ignore[attr-defined]
    streamlit_module.error = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    streamlit_module.rerun = lambda: None  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)


def test_inicio_preserves_cached_embeddings(monkeypatch) -> None:
    """Importing ``Inicio`` must keep the cached embeddings instance intact."""

    _install_streamlit_stub(monkeypatch)

    import app.common.langchain_module as langchain_module
    from app.common import embeddings_manager

    previous_manager = embeddings_manager.get_embeddings_manager()

    class _SentinelManager:
        def __init__(self) -> None:
            self.marker = object()

        def get_embeddings(self, domain=None):  # pragma: no cover - unused stub
            raise AssertionError("Embeddings should not be requested during the test")

    sentinel_manager = _SentinelManager()
    embeddings_manager.configure_default_manager(sentinel_manager)  # type: ignore[arg-type]

    module_name = "Inicio"
    existing_module = sys.modules.pop(module_name, None)

    try:
        importlib.import_module(module_name)
        assert langchain_module.get_embeddings_manager() is sentinel_manager
    finally:
        embeddings_manager.configure_default_manager(previous_manager)
        if existing_module is not None:
            sys.modules[module_name] = existing_module
        else:
            sys.modules.pop(module_name, None)

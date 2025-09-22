"""Tests ensuring the Inicio page delegates chat queries to the orchestrator."""
from __future__ import annotations

import importlib
import sys
import types
from typing import List

import pytest

from app.agents.base import AgentResponse, AgentTask


class _SessionState(dict):
    """Session state replacement compatible with Streamlit usage."""

    def __getattr__(self, name: str):  # noqa: D401 - behave like ``st.session_state``
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value) -> None:  # noqa: D401 - behave like ``st.session_state``
        self[name] = value


class _Sidebar:
    def __enter__(self) -> "_Sidebar":  # noqa: D401 - context manager support
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: D401 - context manager support
        return False


class _ChatMessage:
    def __init__(self, role: str, log: List[tuple[str, str]]) -> None:
        self.role = role
        self._log = log

    def __enter__(self) -> "_ChatMessage":  # noqa: D401 - context protocol
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: D401 - context protocol
        return False

    def markdown(self, content: str, **_kwargs) -> None:  # noqa: D401 - mimic Streamlit API
        self._log.append((self.role, str(content)))


def _install_streamlit_stub(monkeypatch: pytest.MonkeyPatch, prompt: str) -> types.ModuleType:
    """Register a minimal ``streamlit`` stub supporting the chat workflow."""

    message_log: List[tuple[str, str]] = []
    prompts = [prompt]

    session_state = _SessionState()
    session_state["messages"] = [{"role": "assistant", "content": "Bienvenido"}]

    def _chat_input(_placeholder: str) -> str | None:
        return prompts.pop(0) if prompts else None

    def _selectbox(_label, options, format_func=lambda value: value, index=0, **_kwargs):
        if not options:
            return None
        if not isinstance(index, int) or index < 0 or index >= len(options):
            index = 0
        return options[index]

    def _chat_message(role: str) -> _ChatMessage:
        return _ChatMessage(role, message_log)

    streamlit_module = types.ModuleType("streamlit")
    streamlit_module.session_state = session_state
    streamlit_module.sidebar = _Sidebar()
    streamlit_module.set_page_config = lambda *args, **kwargs: None
    streamlit_module.header = lambda *args, **kwargs: None
    streamlit_module.title = lambda *args, **kwargs: None
    streamlit_module.markdown = lambda *args, **kwargs: None
    streamlit_module.selectbox = _selectbox
    streamlit_module.chat_message = _chat_message
    streamlit_module.chat_input = _chat_input
    streamlit_module.error = lambda *args, **kwargs: None
    streamlit_module.rerun = lambda: None

    monkeypatch.setitem(sys.modules, "streamlit", streamlit_module)
    return streamlit_module


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.calls: List[AgentTask] = []

    def execute(self, task: AgentTask) -> AgentResponse:
        self.calls.append(task)
        return AgentResponse(
            success=True,
            data={"answer": "Respuesta orquestada"},
            metadata={"language": task.get("language")},
        )


def test_inicio_routes_chat_messages_via_orchestrator(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Inicio page must build ``AgentTask`` instances and call the orchestrator."""

    prompt = "¿Cuál es la política vigente?"
    streamlit_stub = _install_streamlit_stub(monkeypatch, prompt)
    orchestrator = _FakeOrchestrator()

    monkeypatch.setattr(
        "app.agents.orchestrator.create_default_orchestrator", lambda: orchestrator
    )

    sys.modules.pop("Inicio", None)
    module = importlib.import_module("Inicio")

    try:
        assert orchestrator.calls, "The orchestrator should receive a task"
        task = orchestrator.calls[0]
        assert task.task_type == "document_query"
        assert task.get("question") == prompt
        assert task.get("language") == "es"
        history = task.get("history")
        assert isinstance(history, list)
        assert history[0]["content"] == "Bienvenido"
        assert history[-1]["content"] == prompt
        assert streamlit_stub.session_state.messages[-1]["content"] == "Respuesta orquestada"
    finally:
        sys.modules.pop("Inicio", None)

"""Unit tests for the specialised troubleshooting code agent."""

from __future__ import annotations

from typing import List

import pytest

from app.agents.base import AgentTask
from app.agents.code import CODE_COLLECTION
from app.agents.code_agent import CodeAgent


class _StubCollection:
    def __init__(self, documents: List[str] | None = None) -> None:
        self.requests: List[tuple[list[str], int]] = []
        self._documents = documents or ["Solución placeholder"]

    def query(self, query_texts: list[str], n_results: int):
        self.requests.append((list(query_texts), n_results))
        return {
            "documents": [list(self._documents)],
            "metadatas": [[{"source": "troubleshooting.md"} for _ in self._documents]],
        }


def test_code_agent_returns_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    """The agent should return normalised matches from the troubleshooting collection."""

    calls: list[tuple[str, str, str]] = []

    def fake_record(agent: str, task_type: str, status: str, **_: object) -> None:
        calls.append((agent, task_type, status))

    monkeypatch.setattr("app.agents.code_agent.agent.record_agent_invocation", fake_record)

    collection = _StubCollection(documents=["Reiniciar el servicio", "Verificar dependencias"])
    agent = CodeAgent(collection_resolver=lambda _: collection)

    response = agent.handle(
        AgentTask(
            task_type="code_troubleshooting",
            payload={"query": "Error en despliegue", "limit": 1, "language": "es"},
        )
    )

    assert response.success is True
    assert response.data == {
        "collection": CODE_COLLECTION,
        "matches": [
            {"content": "Reiniciar el servicio", "metadata": {"source": "troubleshooting.md"}},
            {"content": "Verificar dependencias", "metadata": {"source": "troubleshooting.md"}},
        ],
    }
    assert response.metadata == {
        "query": "Error en despliegue",
        "match_count": 2,
        "language": "es",
    }
    assert calls == [("code_agent", "code_troubleshooting", "success")]
    assert collection.requests == [(["Error en despliegue"], 1)]


def test_code_agent_requires_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing prompts should be reported as invalid payloads."""

    calls: list[tuple[str, str, str]] = []

    def fake_record(agent: str, task_type: str, status: str, **_: object) -> None:
        calls.append((agent, task_type, status))

    monkeypatch.setattr("app.agents.code_agent.agent.record_agent_invocation", fake_record)

    agent = CodeAgent(retriever=lambda *_: [])
    response = agent.handle(AgentTask(task_type="code_troubleshooting", payload={}))

    assert response.success is False
    assert response.error == "query_missing"
    assert calls == [("code_agent", "code_troubleshooting", "invalid")]


def test_code_agent_handles_collection_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failures when querying the collection should surface a controlled error."""

    calls: list[tuple[str, str, str]] = []

    def fake_record(agent: str, task_type: str, status: str, **_: object) -> None:
        calls.append((agent, task_type, status))

    monkeypatch.setattr("app.agents.code_agent.agent.record_agent_invocation", fake_record)

    def failing_retriever(*_: object) -> list[object]:
        raise RuntimeError("collection offline")

    agent = CodeAgent(retriever=failing_retriever)
    response = agent.handle(
        AgentTask(task_type="code_troubleshooting", payload={"query": "timeout"})
    )

    assert response.success is False
    assert response.error == "code_collection_error"
    assert calls == [("code_agent", "code_troubleshooting", "error")]

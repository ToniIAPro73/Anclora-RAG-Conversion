"""Tests ensuring observability hooks do not break agent flows."""

from __future__ import annotations

from typing import List

import pytest

from app.agents.base import AgentTask, BaseFileIngestor
from app.agents.document_agent import DocumentAgent
from app.agents.media_agent import MediaAgent
from app.agents.orchestrator import OrchestratorService
from common.text_normalization import Document


class _StubLoader:
    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        """Test loader that always returns a single document."""

    def load(self) -> List[Document]:  # type: ignore[override]
        return [Document(page_content="contenido", metadata={"source": "stub"})]


def test_ingestor_records_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """The BaseFileIngestor should record metrics for successful loads."""

    calls: list[tuple[str, str, str, int | None]] = []

    def fake_record(domain: str, extension: str, status: str, **kwargs: object) -> None:
        calls.append((domain, extension, status, kwargs.get("document_count")))

    monkeypatch.setattr("app.agents.base.record_ingestion", fake_record)

    ingestor = BaseFileIngestor(domain="documents", collection_name="vectordb", loader_mapping={".txt": (_StubLoader, {})})
    documents = ingestor.load("archivo.txt", ".txt")

    assert len(documents) == 1
    assert calls == [("documents", ".txt", "success", 1)]


def test_document_agent_records_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """DocumentAgent should record the outcome of successful executions."""

    calls: list[tuple[str, str, str, str | None]] = []

    def fake_record(agent: str, task_type: str, status: str, **kwargs: object) -> None:
        calls.append((agent, task_type, status, kwargs.get("language")))

    monkeypatch.setattr("app.agents.document_agent.agent.record_agent_invocation", fake_record)

    agent = DocumentAgent(query_function=lambda *_: "respuesta")
    response = agent.handle(AgentTask(task_type="document_query", payload={"question": "hola", "language": "es"}))

    assert response.success is True
    assert calls == [("document_agent", "document_query", "success", "es")]


def test_document_agent_records_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """DocumentAgent should record invalid payloads without raising errors."""

    calls: list[tuple[str, str, str]] = []

    def fake_record(agent: str, task_type: str, status: str, **kwargs: object) -> None:
        calls.append((agent, task_type, status))

    monkeypatch.setattr("app.agents.document_agent.agent.record_agent_invocation", fake_record)

    agent = DocumentAgent(query_function=lambda *_: "irrelevante")
    response = agent.handle(AgentTask(task_type="document_query", payload={}))

    assert response.success is False
    assert calls == [("document_agent", "document_query", "invalid")]


def test_media_agent_records_flows(monkeypatch: pytest.MonkeyPatch) -> None:
    """MediaAgent instrumentation should track both success and invalid paths."""

    calls: list[tuple[str, str, str]] = []

    def fake_record(agent: str, task_type: str, status: str, **kwargs: object) -> None:
        calls.append((agent, task_type, status))

    monkeypatch.setattr("app.agents.media_agent.agent.record_agent_invocation", fake_record)

    agent = MediaAgent()

    success = agent.handle(AgentTask(task_type="media_transcription", payload={"media": "file.mp4"}))
    invalid = agent.handle(AgentTask(task_type="media_transcription", payload={}))

    assert success.success is True
    assert invalid.success is False
    assert calls == [
        ("media_agent", "media_transcription", "success"),
        ("media_agent", "media_transcription", "invalid"),
    ]


def test_orchestrator_records_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Routing decisions should be emitted regardless of the outcome."""

    calls: list[tuple[str, str]] = []

    def fake_routing(task_type: str, result: str) -> None:
        calls.append((task_type, result))

    monkeypatch.setattr("app.agents.orchestrator.service.record_orchestrator_decision", fake_routing)
    monkeypatch.setattr("app.agents.document_agent.agent.record_agent_invocation", lambda *args, **kwargs: None)

    orchestrator = OrchestratorService(agents=[DocumentAgent(query_function=lambda *_: "ok")])

    orchestrator.execute(AgentTask(task_type="document_query", payload={"question": "hola"}))
    orchestrator.execute(AgentTask(task_type="media_summary", payload={}))

    assert calls == [
        ("document_query", "document_agent"),
        ("media_summary", "unhandled"),
    ]

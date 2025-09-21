"""Basic integration checks for the multi-agent orchestration layer."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.agents.base import AgentTask
from app.agents.document_agent import DocumentAgent
from app.agents.orchestrator import OrchestratorService, document_query_flow


def test_orchestrator_routes_document_tasks() -> None:
    """The orchestrator should delegate document queries to the document agent."""

    query_function = MagicMock(return_value="respuesta contextual")
    orchestrator = OrchestratorService(agents=[DocumentAgent(query_function=query_function)])

    response = orchestrator.execute(
        AgentTask(task_type="document_query", payload={"question": "¿Qué es PBC?"})
    )

    assert response.success is True
    assert response.data == {"answer": "respuesta contextual"}
    query_function.assert_called_once_with("¿Qué es PBC?", None)


def test_orchestrator_returns_error_for_unknown_tasks() -> None:
    """If no agent can handle the request, the orchestrator returns a controlled error."""

    orchestrator = OrchestratorService(agents=[DocumentAgent(query_function=lambda *_: "irrelevant")])

    response = orchestrator.execute(AgentTask(task_type="media_transcription", payload={}))

    assert response.success is False
    assert response.error == "no_agent_for_media_transcription"


def test_document_agent_requires_question() -> None:
    """Document agent should guard against empty payloads."""

    agent = DocumentAgent(query_function=lambda *_: "unused")

    response = agent.handle(AgentTask(task_type="document_query", payload={}))

    assert response.success is False
    assert response.error == "question_missing"


def test_document_flow_helper_uses_provided_orchestrator() -> None:
    """The helper flow should leverage any orchestrator injected for testing purposes."""

    query_function = MagicMock(return_value="respuesta orquestada")
    orchestrator = OrchestratorService(agents=[DocumentAgent(query_function=query_function)])

    response = document_query_flow("Explica el cubo de datos", orchestrator=orchestrator)

    assert response.success is True
    assert response.data == {"answer": "respuesta orquestada"}
    query_function.assert_called_once_with("Explica el cubo de datos", None)

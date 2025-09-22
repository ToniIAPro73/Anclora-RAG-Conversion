"""Basic integration checks for the multi-agent orchestration layer."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.agents.document_agent import DocumentAgent
from app.agents.orchestrator import OrchestratorService, document_query_flow


class _DynamicAgent(BaseAgent):
    def __init__(self, name: str = "dynamic_agent", handled_task: str = "dynamic_task") -> None:
        super().__init__(name=name)
        self._handled_task = handled_task

    def can_handle(self, task: AgentTask) -> bool:
        return task.task_type == self._handled_task

    def handle(self, task: AgentTask) -> AgentResponse:
        return AgentResponse(success=True, data={"handled_by": self.name})


def _dynamic_factory() -> BaseAgent:
    return _DynamicAgent(name="factory_agent", handled_task="factory_task")


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


def test_orchestrator_initialises_agents_from_config() -> None:
    """Agent implementations can be referenced through configuration strings."""

    spec = f"{__name__}:_dynamic_factory"
    orchestrator = OrchestratorService(agent_configs=[spec])

    response = orchestrator.execute(AgentTask(task_type="factory_task", payload={}))

    assert response.success is True
    assert response.data == {"handled_by": "factory_agent"}
    assert orchestrator.available_agents() == ["factory_agent"]


def test_orchestrator_supports_late_registration() -> None:
    """Agents can be registered after instantiation using factories or classes."""

    orchestrator = OrchestratorService()
    agent = orchestrator.register_agent_late(lambda: _DynamicAgent(name="late_agent", handled_task="late_task"))

    assert agent.name == "late_agent"

    response = orchestrator.execute(AgentTask(task_type="late_task", payload={}))

    assert response.success is True
    assert response.data == {"handled_by": "late_agent"}
    assert orchestrator.available_agents() == ["late_agent"]

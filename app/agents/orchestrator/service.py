"""High level orchestration primitives coordinating specialised agents."""

from __future__ import annotations

from collections import OrderedDict
from typing import List, Sequence

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.agents.document_agent import DocumentAgent
from app.agents.media_agent import MediaAgent


class OrchestratorService:
    """Coordinate task delegation between the available agents."""

    def __init__(self, agents: Sequence[BaseAgent] | None = None) -> None:
        self._agents: "OrderedDict[str, BaseAgent]" = OrderedDict()
        if agents:
            for agent in agents:
                self.register_agent(agent)

    def register_agent(self, agent: BaseAgent) -> None:
        """Register or update an agent implementation."""

        self._agents[agent.name] = agent

    def available_agents(self) -> List[str]:
        """Return the registered agent names preserving registration order."""

        return list(self._agents.keys())

    def execute(self, task: AgentTask) -> AgentResponse:
        """Delegate execution to the first agent that declares support."""

        for agent in self._agents.values():
            if agent.can_handle(task):
                return agent.handle(task)

        return AgentResponse(success=False, error=f"no_agent_for_{task.task_type}")


def create_default_orchestrator() -> OrchestratorService:
    """Build an orchestrator with the default agents described in the report."""

    return OrchestratorService(agents=[DocumentAgent(), MediaAgent()])


def document_query_flow(question: str, language: str | None = None, orchestrator: OrchestratorService | None = None) -> AgentResponse:
    """Example flow that routes a document question through the orchestrator.

    The flow performs three simple steps:

    1. Construye la tarea con la consulta y metadatos opcionales (idioma, contexto).
    2. Delegates execution to the orchestrator, which selects the :class:`DocumentAgent`.
    3. Retorna la respuesta estandarizada del agente con el campo ``answer`` listo para la UI o APIs.
    """

    service = orchestrator or create_default_orchestrator()
    task = AgentTask(task_type="document_query", payload={"question": question, "language": language})
    return service.execute(task)

"""High level orchestration primitives coordinating specialised agents."""

from __future__ import annotations

from collections import OrderedDict
from importlib import import_module
import inspect
from typing import Callable, Iterable, List, Sequence, Type, Union

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.agents.code_agent import CodeAgent
from app.agents.document_agent import DocumentAgent
from app.agents.media_agent import MediaAgent
from app.agents.content_analyzer_agent import ContentAnalyzerAgent
from app.agents.smart_converter_agent import SmartConverterAgent
from common.observability import record_orchestrator_decision


class OrchestratorService:
    """Coordinate task delegation between the available agents."""

    AgentConfig = Union[
        BaseAgent,
        Type[BaseAgent],
        Callable[[], BaseAgent],
        str,
    ]

    def __init__(
        self,
        agents: Sequence[BaseAgent] | None = None,
        agent_configs: Sequence[AgentConfig] | None = None,
    ) -> None:
        self._agents: "OrderedDict[str, BaseAgent]" = OrderedDict()
        if agents:
            for agent in agents:
                self.register_agent(agent)
        if agent_configs:
            self.register_agents_from_config(agent_configs)

    def register_agent(self, agent: BaseAgent) -> None:
        """Register or update an agent implementation."""

        self._agents[agent.name] = agent

    def register_agent_late(self, agent_config: AgentConfig) -> BaseAgent:
        """Instantiate and register an agent from configuration at runtime."""

        agent = self._build_agent(agent_config)
        self.register_agent(agent)
        return agent

    def register_agents_from_config(self, configs: Iterable[AgentConfig]) -> None:
        """Register multiple agents from configuration entries."""

        for config in configs:
            self.register_agent_late(config)

    def available_agents(self) -> List[str]:
        """Return the registered agent names preserving registration order."""

        return list(self._agents.keys())

    def execute(self, task: AgentTask) -> AgentResponse:
        """Delegate execution to the first agent that declares support."""

        for agent in self._agents.values():
            if agent.can_handle(task):
                record_orchestrator_decision(task.task_type, agent.name)
                return agent.handle(task)

        record_orchestrator_decision(task.task_type, "unhandled")
        return AgentResponse(success=False, error=f"no_agent_for_{task.task_type}")

    def _build_agent(self, config: AgentConfig) -> BaseAgent:
        if isinstance(config, BaseAgent):
            return config

        if inspect.isclass(config) and issubclass(config, BaseAgent):
            return config()

        if callable(config):
            candidate = config()
            if not isinstance(candidate, BaseAgent):
                raise TypeError("Agent factory did not return a BaseAgent instance")
            return candidate

        if isinstance(config, str):
            imported = self._import_from_string(config)
            return self._build_agent(imported)

        raise TypeError(f"Unsupported agent configuration: {config!r}")

    @staticmethod
    def _import_from_string(path: str) -> object:
        cleaned = path.strip()
        if not cleaned:
            raise ValueError("Empty agent configuration entry")

        module_path: str
        attr_path: str
        if ":" in cleaned:
            module_path, attr_path = cleaned.split(":", 1)
        else:
            module_path, _, attr_path = cleaned.rpartition(".")
        if not module_path or not attr_path:
            raise ValueError(f"Invalid agent specification: {path!r}")

        module = import_module(module_path)
        attribute: object = module
        for part in attr_path.split("."):
            attribute = getattr(attribute, part)
        return attribute


def create_default_orchestrator() -> OrchestratorService:
    """Build an orchestrator with the default agents described in the report."""

    return OrchestratorService(agents=[
        DocumentAgent(),
        MediaAgent(),
        CodeAgent(),
        ContentAnalyzerAgent(),
        SmartConverterAgent()
    ])


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

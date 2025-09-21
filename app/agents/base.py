"""Shared contracts for agent collaboration within the RAG platform."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class AgentTask:
    """Describe una tarea que puede ser delegada a un agente especializado."""

    task_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Utility helper to read values from payload or context."""

        if key in self.payload:
            return self.payload.get(key, default)
        if key in self.context:
            return self.context.get(key, default)
        return default


@dataclass(slots=True)
class AgentResponse:
    """Resultado estandarizado de la ejecución de una tarea."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Interfaz base que todos los agentes deben implementar."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        """Nombre descriptivo del agente."""

        return self._name

    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool:
        """Indica si el agente puede gestionar la tarea solicitada."""

    @abstractmethod
    def handle(self, task: AgentTask) -> AgentResponse:
        """Procesa la tarea delegada y devuelve un :class:`AgentResponse`."""

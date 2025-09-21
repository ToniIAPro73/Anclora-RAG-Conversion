"""Shared building blocks for RAG agents and ingestors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Type

from common.text_normalization import Document


LoaderConfig = Tuple[Type[object], Dict[str, object]]


@dataclass(slots=True)
class AgentResponse:
    """Standard response format for agent interactions."""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentTask:
    """Encapsulates the payload that an agent receives."""

    task_type: str
    payload: Dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_type, str) or not self.task_type.strip():
            raise ValueError("task_type must be a non-empty string")
        self.task_type = self.task_type.strip()
        if self.payload is None:
            self.payload = {}
        elif not isinstance(self.payload, dict):
            self.payload = dict(self.payload)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an item from the payload with ``default`` fallback."""

        return self.payload.get(key, default) if self.payload is not None else default

    def __getitem__(self, key: str) -> Any:
        if self.payload is None:
            raise KeyError(key)
        return self.payload[key]


class BaseAgent:
    """Interface that all orchestrated agents must implement."""

    name: str

    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("Agent name must be provided")
        self.name = name

    def can_handle(self, task: AgentTask) -> bool:
        """Return ``True`` if the agent can process *task*."""

        raise NotImplementedError

    def handle(self, task: AgentTask) -> AgentResponse:
        """Process *task* and return a standardised response."""

        raise NotImplementedError


@dataclass
class BaseFileIngestor:
    """Base class shared by domain specific ingestors."""

    domain: str
    collection_name: str
    loader_mapping: Mapping[str, LoaderConfig]

    def supports_extension(self, extension: str) -> bool:
        """Return ``True`` if *extension* can be processed by this ingestor."""

        return extension in self.loader_mapping

    @property
    def extensions(self) -> Iterable[str]:
        """Iterable view of supported file extensions."""

        return self.loader_mapping.keys()

    def load(self, file_path: str, extension: str) -> List[Document]:
        """Load ``Document`` instances from *file_path* using the proper loader."""

        if extension not in self.loader_mapping:
            raise ValueError(f"Extension '{extension}' not supported by {self.domain} ingestor")

        loader_class, loader_kwargs = self.loader_mapping[extension]
        loader = loader_class(file_path, **loader_kwargs)
        return loader.load()


__all__ = [
    "AgentResponse",
    "AgentTask",
    "BaseAgent",
    "BaseFileIngestor",
    "LoaderConfig",
]


"""Shared building blocks for RAG agents and ingestors."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Type
from common.observability import record_ingestion
from common.text_normalization import Document

LoaderConfig = Tuple[Type[object], Dict[str, object]]

@dataclass(frozen=True)
class AgentTask:
    """Payload that describes a task delegated to an agent."""

    task_type: str
    payload: Mapping[str, Any]

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Expose the underlying payload like a dictionary."""

        return self.payload.get(key, default)


@dataclass
class AgentResponse:
    """Standard structure returned by all agents."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAgent:
    """Common interface for all specialised agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    def can_handle(self, task: AgentTask) -> bool:  # pragma: no cover - abstract behaviour
        raise NotImplementedError

    def handle(self, task: AgentTask) -> AgentResponse:  # pragma: no cover - abstract behaviour
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
            record_ingestion(self.domain, extension, "unsupported_extension")
            raise ValueError(f"Extension '{extension}' not supported by {self.domain} ingestor")

        loader_class, loader_kwargs = self.loader_mapping[extension]
        loader = loader_class(file_path, **loader_kwargs)

        start_time = time.perf_counter()

        try:
            documents = loader.load()
        except Exception:
            record_ingestion(
                self.domain,
                extension,
                "error",
                duration_seconds=time.perf_counter() - start_time,
            )
            raise

        record_ingestion(
            self.domain,
            extension,
            "success",
            duration_seconds=time.perf_counter() - start_time,
            document_count=len(documents) if isinstance(documents, list) else None,
        )

        return documents

__all__ = [
    "AgentResponse",
    "AgentTask",
    "BaseAgent",
    "BaseFileIngestor",
    "LoaderConfig",
]
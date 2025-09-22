"""Agent focused on troubleshooting workflows for code snippets and logs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, List, Mapping, MutableMapping, Sequence

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.agents.code import CODE_COLLECTION
from app.common.observability import record_agent_invocation


_ContextItem = Mapping[str, Any]
_Retriever = Callable[[str, int], Sequence[_ContextItem]]
_CollectionResolver = Callable[[str], Any]


@dataclass(frozen=True)
class CodeAgentConfig:
    """Configuration options for :class:`CodeAgent`."""

    collection_name: str = CODE_COLLECTION
    max_results: int = 3


class CodeAgent(BaseAgent):
    """Retrieve troubleshooting content from the code knowledge base."""

    SUPPORTED_TASKS = {"code_troubleshooting"}

    def __init__(
        self,
        config: CodeAgentConfig | None = None,
        retriever: _Retriever | None = None,
        collection_resolver: _CollectionResolver | None = None,
    ) -> None:
        super().__init__(name="code_agent")
        self._config = config or CodeAgentConfig()
        self._retriever = retriever
        if retriever is None:
            self._collection_resolver = collection_resolver or self._default_collection_resolver
        else:
            self._collection_resolver = collection_resolver

    def can_handle(self, task: AgentTask) -> bool:
        return task.task_type in self.SUPPORTED_TASKS

    def handle(self, task: AgentTask) -> AgentResponse:
        query = task.get("query") or task.get("question")
        limit = self._resolve_limit(task.get("limit"))
        language = task.get("language")
        language_label = str(language).strip() if isinstance(language, str) and language.strip() else None

        start_time = time.perf_counter()

        if not query:
            record_agent_invocation(
                self.name,
                task.task_type,
                "invalid",
                duration_seconds=time.perf_counter() - start_time,
                language=language_label,
            )
            return AgentResponse(success=False, error="query_missing")

        try:
            matches = self._retrieve_matches(str(query), limit)
        except Exception:
            record_agent_invocation(
                self.name,
                task.task_type,
                "error",
                duration_seconds=time.perf_counter() - start_time,
                language=language_label,
            )
            return AgentResponse(success=False, error="code_collection_error")

        record_agent_invocation(
            self.name,
            task.task_type,
            "success",
            duration_seconds=time.perf_counter() - start_time,
            language=language_label,
        )

        normalised_matches = self._normalise_matches(matches)

        return AgentResponse(
            success=True,
            data={
                "collection": self._config.collection_name,
                "matches": normalised_matches,
            },
            metadata={
                "query": str(query),
                "match_count": len(normalised_matches),
                "language": language_label,
            },
        )

    def _resolve_limit(self, raw_limit: Any) -> int:
        if isinstance(raw_limit, int) and raw_limit > 0:
            return raw_limit
        if isinstance(raw_limit, str):
            try:
                parsed = int(raw_limit.strip())
            except ValueError:
                parsed = 0
            if parsed > 0:
                return parsed
        return max(int(self._config.max_results), 1)

    def _retrieve_matches(self, query: str, limit: int) -> Sequence[_ContextItem]:
        if self._retriever is not None:
            return self._retriever(query, limit)

        resolver = self._collection_resolver
        if resolver is None:
            raise RuntimeError("collection_resolver_missing")

        collection = resolver(self._config.collection_name)
        raw_results = collection.query(query_texts=[query], n_results=max(limit, 1))
        return self._convert_collection_results(raw_results)

    def _normalise_matches(self, matches: Sequence[_ContextItem]) -> List[dict[str, Any]]:
        normalised: List[dict[str, Any]] = []
        for match in matches:
            if isinstance(match, Mapping):
                content = match.get("content")
                metadata_value = match.get("metadata")
            else:
                content = match
                metadata_value = None

            if not isinstance(content, str):
                content = "" if content is None else str(content)

            metadata: MutableMapping[str, Any]
            if isinstance(metadata_value, Mapping):
                metadata = dict(metadata_value)
            else:
                metadata = {}
            normalised.append({"content": content, "metadata": dict(metadata)})
        return normalised

    def _convert_collection_results(self, results: Mapping[str, Any]) -> Sequence[_ContextItem]:
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []

        if documents and isinstance(documents[0], list):
            documents = documents[0]
        if metadatas and isinstance(metadatas[0], list):
            metadatas = metadatas[0]

        converted: List[dict[str, Any]] = []
        for index, content in enumerate(documents):
            metadata: Mapping[str, Any]
            if index < len(metadatas) and isinstance(metadatas[index], Mapping):
                metadata = metadatas[index]
            else:
                metadata = {}
            converted.append({"content": content, "metadata": dict(metadata)})
        return converted

    @staticmethod
    def _default_collection_resolver(collection_name: str) -> Any:
        from app.common.constants import CHROMA_SETTINGS

        return CHROMA_SETTINGS.get_or_create_collection(collection_name)


__all__ = ["CodeAgent", "CodeAgentConfig"]

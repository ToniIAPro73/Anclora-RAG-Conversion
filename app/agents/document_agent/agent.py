"""Document-centric agent implementation leveraging the LangChain RAG core."""

from __future__ import annotations

import time
from typing import Callable, Optional

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.common import langchain_module
from common.observability import record_agent_invocation

QueryFunction = Callable[[str, Optional[str]], str]


class DocumentAgent(BaseAgent):
    """Agent responsible for answering document-related questions via RAG."""

    def __init__(self, query_function: QueryFunction | None = None) -> None:
        super().__init__(name="document_agent")
        self._query_function: QueryFunction = query_function or langchain_module.response

    def can_handle(self, task: AgentTask) -> bool:
        """Only handle ``document_query`` tasks."""

        return task.task_type == "document_query"

    def handle(self, task: AgentTask) -> AgentResponse:
        """Run the query through the RAG pipeline and standardise the response."""

        question = task.get("question")
        language = task.get("language")

        start_time = time.perf_counter()
        language_label = language if isinstance(language, str) else None

        if not question:
            record_agent_invocation(
                self.name,
                task.task_type,
                "invalid",
                duration_seconds=time.perf_counter() - start_time,
                language=language_label,
            )
            return AgentResponse(success=False, error="question_missing")

        try:
            answer = self._query_function(str(question), language if language else None)
        except Exception as exc:  # pragma: no cover - defensive branch
            record_agent_invocation(
                self.name,
                task.task_type,
                "error",
                duration_seconds=time.perf_counter() - start_time,
                language=language_label,
            )
            return AgentResponse(success=False, error=str(exc))

        record_agent_invocation(
            self.name,
            task.task_type,
            "success",
            duration_seconds=time.perf_counter() - start_time,
            language=language_label,
        )

        return AgentResponse(
            success=True,
            data={"answer": answer},
            metadata={"language": language},
        )

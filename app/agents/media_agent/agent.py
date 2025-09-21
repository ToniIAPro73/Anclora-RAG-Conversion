"""Media agent offering lightweight placeholders for future multimedia workflows."""

from __future__ import annotations

import time

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from common.observability import record_agent_invocation


class MediaAgent(BaseAgent):
    """Provide basic responses for media-oriented tasks until a full pipeline is added."""

    SUPPORTED_TASKS = {"media_transcription", "media_summary"}

    def __init__(self) -> None:
        super().__init__(name="media_agent")

    def can_handle(self, task: AgentTask) -> bool:
        return task.task_type in self.SUPPORTED_TASKS

    def handle(self, task: AgentTask) -> AgentResponse:
        media_ref = task.get("media")
        start_time = time.perf_counter()

        if not media_ref:
            record_agent_invocation(
                self.name,
                task.task_type,
                "invalid",
                duration_seconds=time.perf_counter() - start_time,
            )
            return AgentResponse(success=False, error="media_reference_missing")

        record_agent_invocation(
            self.name,
            task.task_type,
            "success",
            duration_seconds=time.perf_counter() - start_time,
        )

        return AgentResponse(
            success=True,
            data={
                "message": "Media task acknowledged. Implement post-processing pipeline to extend capabilities.",
                "media": media_ref,
            },
        )

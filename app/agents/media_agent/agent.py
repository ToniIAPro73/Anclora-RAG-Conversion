"""Media agent offering lightweight placeholders for future multimedia workflows."""

from __future__ import annotations

from app.agents.base import AgentResponse, AgentTask, BaseAgent


class MediaAgent(BaseAgent):
    """Provide basic responses for media-oriented tasks until a full pipeline is added."""

    SUPPORTED_TASKS = {"media_transcription", "media_summary"}

    def __init__(self) -> None:
        super().__init__(name="media_agent")

    def can_handle(self, task: AgentTask) -> bool:
        return task.task_type in self.SUPPORTED_TASKS

    def handle(self, task: AgentTask) -> AgentResponse:
        media_ref = task.get("media")
        if not media_ref:
            return AgentResponse(success=False, error="media_reference_missing")

        return AgentResponse(
            success=True,
            data={
                "message": "Media task acknowledged. Implement post-processing pipeline to extend capabilities.",
                "media": media_ref,
            },
        )

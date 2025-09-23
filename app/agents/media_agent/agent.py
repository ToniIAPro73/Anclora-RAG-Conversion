"""Media agent offering lightweight placeholders for future multimedia workflows."""

from __future__ import annotations

import time

import sys
import os

# Add the app directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from agents.base import AgentResponse, AgentTask, BaseAgent
from common.observability import record_agent_invocation


class MediaAgent(BaseAgent):
    """Provide basic responses for media-oriented tasks until a full pipeline is added."""

    SUPPORTED_TASKS = {"media_transcription", "media_summary", "media_pipeline"}

    def __init__(self) -> None:
        super().__init__(name="media_agent")

    def can_handle(self, task: AgentTask) -> bool:
        return task.task_type in self.SUPPORTED_TASKS

    def handle(self, task: AgentTask) -> AgentResponse:
        media_ref = task.get("media")
        instructions = self._normalise_instructions(task)
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

        placeholders = [
            {
                "instruction": instruction,
                "status": "pending",
                "detail": (
                    "Placeholder response. Configure the media processing pipeline to "
                    f"generate '{instruction}' outputs."
                ),
            }
            for instruction in instructions
        ]

        return AgentResponse(
            success=True,
            data={
                "media": media_ref,
                "results": placeholders,
            },
            metadata={
                "instructions": instructions,
                "response_type": "placeholder",
            },
        )

    def _normalise_instructions(self, task: AgentTask) -> list[str]:
        instructions = task.get("instructions")

        if isinstance(instructions, str):
            values = [instructions]
        elif isinstance(instructions, (list, tuple)):
            values = [value for value in instructions if isinstance(value, str)]
        else:
            values = []

        if values:
            return [value.strip().lower() for value in values if value.strip()]

        default = {
            "media_transcription": ["transcription"],
            "media_summary": ["summary"],
            "media_pipeline": ["transcription", "summary"],
        }
        return default.get(task.task_type, ["transcription"])

"""Regression harness validating multi-agent interactions."""
from __future__ import annotations

from typing import Callable, List

import pytest

from app.agents.base import AgentTask
from app.agents.document_agent import DocumentAgent
from app.agents.media_agent import MediaAgent

from .agent_harness import AgentRegressionHarness, AgentScenario, ScenarioContext


def _document_setup(expected_answer: str) -> Callable[[ScenarioContext], None]:
    def _configure(context: ScenarioContext) -> None:
        context.set_documents(
            ("Resumen ejecutivo trimestral", "conversion_rules"),
            ("Registro de incidencias resueltas", "troubleshooting"),
            ("Storyboard multimedia aprobado", "multimedia_assets"),
        )

        def _llm_callback(payload: dict) -> str:
            assert "trimestral" in payload["question"]
            formatted_context = payload["context"]
            for fragment in ("Resumen ejecutivo", "Registro de incidencias", "Storyboard multimedia"):
                assert fragment in formatted_context
            return expected_answer

        context.set_llm_callback(_llm_callback)

    return _configure


def _document_quality(response) -> None:
    assert response.metadata == {"language": "es"}
    assert response.data["answer"].endswith("español.")


def _media_quality(response) -> None:
    assert response.data["message"].startswith("Media task acknowledged")


SCENARIOS: List[AgentScenario] = [
    AgentScenario(
        name="document_agent_resumen",
        agent_factory=lambda: DocumentAgent(),
        task=AgentTask(task_type="document_query", payload={"question": " Resumen trimestral? ", "language": "es"}),
        setup=_document_setup("Respuesta consolidada en español."),
        expected_success=True,
        expected_answer="Respuesta consolidada en español.",
        max_latency=0.25,
        min_context_docs=3,
        expected_collections={
            "conversion_rules": 1,
            "troubleshooting": 1,
            "multimedia_assets": 1,
        },
        expected_domains={"documents": 1, "code": 1, "multimedia": 1},
        quality_check=_document_quality,
    ),
    AgentScenario(
        name="media_agent_summary",
        agent_factory=lambda: MediaAgent(),
        task=AgentTask(task_type="media_summary", payload={"media": "gs://bucket/demo.mp4"}),
        expected_success=True,
        max_latency=0.1,
        quality_check=_media_quality,
    ),
    AgentScenario(
        name="media_agent_missing_media",
        agent_factory=lambda: MediaAgent(),
        task=AgentTask(task_type="media_summary", payload={}),
        expected_success=False,
        max_latency=0.1,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.name)
def test_agent_regression_harness_scenarios(rag_test_harness, scenario):
    module, harness = rag_test_harness
    harness.set_docs()  # ensure default state is controlled per scenario

    regression = AgentRegressionHarness(module, harness)
    result = regression.run_scenario(scenario)

    assert result.passed, f"{scenario.name} falló validaciones: {result.issues}"

    if scenario.expected_success:
        assert result.response.success
    else:
        assert not result.response.success

    if scenario.expected_collections:
        assert result.context_collections == scenario.expected_collections

    if scenario.expected_domains:
        assert result.domain_documents == scenario.expected_domains

    if scenario.expected_answer is not None and result.response.success:
        assert result.response.data["answer"] == scenario.expected_answer

    assert result.duration <= scenario.max_latency + 0.05  # pequeña tolerancia


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.name)
def test_agent_regression_harness_summary_is_stable(rag_test_harness, scenario):
    module, harness = rag_test_harness
    harness.set_docs()
    regression = AgentRegressionHarness(module, harness)
    result = regression.run_scenario(scenario)

    # Los escenarios deben exponer información de métricas para dashboards.
    assert isinstance(result.knowledge_base, dict)
    assert result.metrics_payload is not None
    if scenario.expected_success:
        assert result.response.success


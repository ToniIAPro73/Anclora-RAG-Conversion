"""Regression harness that validates representative agent flows."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from app.agents.base import AgentResponse, AgentTask, BaseAgent


@dataclass
class ScenarioContext:
    """Provide helpers to configure scenarios before executing them."""

    module: Any
    harness: Any

    def set_documents(self, *entries: str | tuple[str, str]) -> None:
        """Delegate to the underlying test harness to configure documents."""

        self.harness.set_docs(*entries)

    def set_llm_callback(self, callback: Callable[[dict], str]) -> None:
        """Assign the LLM callback used by the patched RAG pipeline."""

        self.harness.set_llm_callback(callback)

    @property
    def collection_domains(self) -> Mapping[str, str]:
        """Expose the mapping between collection names and business domains."""

        return getattr(self.harness, "collection_domains", {})


@dataclass
class AgentScenario:
    """Describe a regression scenario for a specialised agent."""

    name: str
    agent_factory: Callable[[], BaseAgent]
    task: AgentTask
    setup: Callable[[ScenarioContext], None] = lambda ctx: None
    expected_success: bool = True
    expected_answer: Optional[str] = None
    max_latency: float = 0.5
    min_context_docs: Optional[int] = None
    expected_collections: Optional[Mapping[str, int]] = None
    expected_domains: Optional[Mapping[str, int]] = None
    quality_check: Optional[Callable[[AgentResponse], None]] = None


@dataclass
class ScenarioResult:
    """Outcome for a regression scenario including validation notes."""

    scenario: AgentScenario
    response: AgentResponse
    duration: float
    context_documents: Optional[int]
    context_collections: Dict[str, int]
    domain_documents: Dict[str, int]
    knowledge_base: Dict[str, int]
    metrics_payload: Dict[str, Any]
    issues: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return ``True`` when no validation issues were detected."""

        return not self.issues


class AgentRegressionHarness:
    """Execute agent scenarios and collect validation metadata."""

    def __init__(self, module: Any, harness: Any) -> None:
        self._module = module
        self._harness = harness

    def _reset_state(self) -> None:
        """Reset harness internal state before running a scenario."""

        self._harness.prompt_inputs.clear()
        self._harness.llm_invocations.clear()
        self._harness.last_metrics = {}
        self._harness.context_breakdown = {}

    def _domain_breakdown(
        self,
        collections: Mapping[str, int],
        domain_map: Mapping[str, str],
    ) -> Dict[str, int]:
        breakdown: Dict[str, int] = {}
        for collection, count in collections.items():
            domain = domain_map.get(collection) or domain_map.get(collection.lower(), "unknown")
            breakdown[domain] = breakdown.get(domain, 0) + int(count)
        return breakdown

    def run_scenario(self, scenario: AgentScenario) -> ScenarioResult:
        """Execute a single regression scenario and evaluate heuristics."""

        self._reset_state()
        context = ScenarioContext(module=self._module, harness=self._harness)
        scenario.setup(context)
        agent = scenario.agent_factory()

        start = time.perf_counter()
        response = agent.handle(scenario.task)
        duration = time.perf_counter() - start

        metrics_kwargs: Dict[str, Any] = {}
        if isinstance(self._harness.last_metrics, dict):
            metrics_kwargs = dict(self._harness.last_metrics.get("kwargs", {}))

        context_documents = metrics_kwargs.get("context_documents")
        context_collections: Dict[str, int] = {}
        raw_context_collections = metrics_kwargs.get("context_collections")
        if isinstance(raw_context_collections, Mapping):
            context_collections = {str(k): int(v) for k, v in raw_context_collections.items()}
        elif isinstance(self._harness.context_breakdown, Mapping):
            context_collections = {str(k): int(v) for k, v in self._harness.context_breakdown.items()}

        if context_documents is None and context_collections:
            context_documents = int(sum(context_collections.values()))

        knowledge_base_collections: Dict[str, int] = {}
        raw_kb = metrics_kwargs.get("knowledge_base_collections")
        if isinstance(raw_kb, Mapping):
            knowledge_base_collections = {
                str(k): int(v) for k, v in raw_kb.items()
            }
        else:
            knowledge_base_collections = {
                str(name): int(count)
                for name, count in getattr(self._harness, "collection_sizes", {}).items()
            }

        collection_domains = metrics_kwargs.get("collection_domains") or context.collection_domains
        domain_documents = self._domain_breakdown(context_collections, collection_domains)

        result = ScenarioResult(
            scenario=scenario,
            response=response,
            duration=duration,
            context_documents=context_documents,
            context_collections=context_collections,
            domain_documents=domain_documents,
            knowledge_base=knowledge_base_collections,
            metrics_payload=metrics_kwargs,
        )

        self._evaluate(result)
        return result

    def _evaluate(self, result: ScenarioResult) -> None:
        """Populate ``issues`` with any validation warnings for a scenario."""

        scenario = result.scenario
        response = result.response

        if scenario.expected_success != response.success:
            result.issues.append(
                "success_mismatch: se esperaba %s y se obtuvo %s"
                % (scenario.expected_success, response.success)
            )

        if scenario.expected_answer is not None:
            answer = None
            if response.data:
                answer = response.data.get("answer")
            if answer != scenario.expected_answer:
                result.issues.append(
                    "respuesta_unexpected: %r" % (answer,)
                )

        if result.duration > scenario.max_latency:
            result.issues.append(
                "latencia_superior_al_umbral: %.4fs > %.4fs"
                % (result.duration, scenario.max_latency)
            )

        total_context = result.context_documents or 0
        if scenario.min_context_docs is not None and total_context < scenario.min_context_docs:
            result.issues.append(
                "contexto_insuficiente: %s < %s"
                % (total_context, scenario.min_context_docs)
            )

        if scenario.expected_collections is not None:
            for collection, expected in scenario.expected_collections.items():
                actual = result.context_collections.get(collection, 0)
                if actual != expected:
                    result.issues.append(
                        f"coleccion_{collection}_mismatch: esperado {expected}, obtenido {actual}"
                    )

        if scenario.expected_domains is not None:
            for domain, expected in scenario.expected_domains.items():
                actual = result.domain_documents.get(domain, 0)
                if actual != expected:
                    result.issues.append(
                        f"dominio_{domain}_mismatch: esperado {expected}, obtenido {actual}"
                    )

        if scenario.quality_check is not None:
            try:
                scenario.quality_check(response)
            except AssertionError as exc:  # pragma: no cover - quality hooks may assert
                result.issues.append(str(exc))

    def run(self, scenarios: Iterable[AgentScenario]) -> List[ScenarioResult]:
        """Execute multiple scenarios and return their results."""

        return [self.run_scenario(scenario) for scenario in scenarios]


__all__ = [
    "AgentRegressionHarness",
    "AgentScenario",
    "ScenarioContext",
    "ScenarioResult",
]

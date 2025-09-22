"""Regression harness runner covering document, media, code and legal agents."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

_AGENTS_DIR = Path(__file__).resolve().parents[2] / "app" / "agents"
_PROJECT_ROOT = _AGENTS_DIR.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_APP_DIR = _PROJECT_ROOT / "app"
if _APP_DIR.is_dir() and str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
if (
    not (_AGENTS_DIR / "code.py").exists()
    and not (_AGENTS_DIR / "code" / "__init__.py").exists()
    and "app.agents.code" not in sys.modules
):
    code_stub = types.ModuleType("app.agents.code")
    code_stub.CODE_COLLECTION = "troubleshooting"
    sys.modules["app.agents.code"] = code_stub

from app.agents.base import AgentResponse, AgentTask
try:  # pragma: no cover - optional stub for environments without app.agents.code
    from app.agents.code_agent import CodeAgent, CodeAgentConfig
except ModuleNotFoundError as exc:  # pragma: no cover - executed en entornos sin alias
    if exc.name != "app.agents.code":
        raise

    code_module = types.ModuleType("app.agents.code")
    code_module.CODE_COLLECTION = "troubleshooting"
    sys.modules["app.agents.code"] = code_module
    sys.modules.pop("app.agents.code_agent", None)

    from app.agents.code_agent import CodeAgent, CodeAgentConfig
from app.agents.document_agent import DocumentAgent
from app.agents.media_agent import MediaAgent

from .agent_harness import AgentRegressionHarness, AgentScenario, ScenarioContext, ScenarioResult
from .conftest import build_regression_harness

DEFAULT_SUITE_DEFINITION: Mapping[str, Mapping[str, Any]] = {
    "document": {
        "name": "document_agent_regression",
        "agent": "document",
        "task": {
            "task_type": "document_query",
            "payload": {
                "question": "¿Cuál es el resumen ejecutivo aprobado para el último trimestre?",
                "language": "es",
            },
        },
        "documents": [
            {
                "text": "Resumen ejecutivo trimestral con métricas clave y riesgos mitigados.",
                "collection": "conversion_rules",
            },
            {
                "text": "Registro de incidencias resueltas durante el sprint de soporte.",
                "collection": "troubleshooting",
            },
            {
                "text": "Storyboard multimedia aprobado con mensajes destacados para clientes.",
                "collection": "multimedia_assets",
            },
        ],
        "llm": {
            "answer": "Resumen consolidado trimestral listo para comunicar a los stakeholders.",
            "context_fragments": [
                "Resumen ejecutivo trimestral",
                "incidencias resueltas",
                "Storyboard multimedia",
            ],
        },
        "thresholds": {"max_latency": 0.35, "min_context_docs": 3},
        "expected_collections": {
            "conversion_rules": 1,
            "troubleshooting": 1,
            "multimedia_assets": 1,
        },
        "expected_domains": {"documents": 1, "code": 1, "multimedia": 1},
        "quality": {
            "language": "es",
            "answer_contains": ["Resumen consolidado", "stakeholders"],
        },
    },
    "media": {
        "name": "media_agent_regression",
        "agent": "media",
        "task": {
            "task_type": "media_summary",
            "payload": {
                "media": "gs://demo/campania-lanzamiento.mp4",
                "instructions": ["summary", "transcription"],
            },
        },
        "thresholds": {"max_latency": 0.05},
        "quality": {
            "expected_instructions": ["summary", "transcription"],
            "response_type": "placeholder",
        },
    },
    "code": {
        "name": "code_agent_regression",
        "agent": "code",
        "task": {
            "task_type": "code_troubleshooting",
            "payload": {
                "query": "Error de despliegue en el servicio de facturación",
                "language": "es",
                "limit": 2,
            },
        },
        "matches": [
            {
                "content": "Reiniciar el servicio de facturación y validar logs de arranque.",
                "metadata": {"source": "troubleshooting.md", "severity": "medium"},
            },
            {
                "content": "Verificar dependencias externas y limpiar caché de despliegue.",
                "metadata": {"source": "troubleshooting.md", "severity": "medium"},
            },
        ],
        "thresholds": {"max_latency": 0.05, "min_matches": 2},
        "quality": {
            "collection": "troubleshooting",
            "language": "es",
        },
    },
    "legal": {
        "name": "legal_agent_regression",
        "agent": "legal",
        "task": {
            "task_type": "legal_query",
            "payload": {
                "question": "¿Cuál es la cláusula vigente para cancelaciones anticipadas?",
                "language": "es",
            },
        },
        "documents": [
            {
                "text": "Cláusula 12 - Cancelaciones anticipadas: requiere aviso con 30 días.",
                "collection": "legal_repository",
            },
            {
                "text": "Guía operativa para orientar la comunicación con clientes regulados.",
                "collection": "conversion_rules",
            },
        ],
        "metadata": {"collections": ["legal_repository"], "prompt_type": "legal"},
        "llm": {
            "answer": "La cláusula vigente de cancelaciones exige aviso con 30 días y validación legal.",
            "context_fragments": ["Cláusula 12", "Cancelaciones anticipadas"],
        },
        "thresholds": {"max_latency": 0.35, "min_context_docs": 1},
        "expected_collections": {"legal_repository": 1},
        "expected_domains": {"legal": 1},
        "quality": {
            "language": "es",
            "enforce_prompt_variant": "legal",
        },
    },
}


@dataclass
class ScenarioBlueprint:
    """Bind an :class:`AgentScenario` with metadata used for reporting."""

    agent: str
    name: str
    thresholds: Mapping[str, Any]
    scenario: AgentScenario


@dataclass
class ScenarioRun:
    """Couple the executed scenario result with its blueprint."""

    blueprint: ScenarioBlueprint
    result: ScenarioResult


@dataclass
class SuiteReport:
    """Aggregate the regression results across all configured agents."""

    runs: List[ScenarioRun]

    @property
    def passed(self) -> bool:
        return all(run.result.passed for run in self.runs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the suite report into a JSON-friendly payload."""

        scenarios: List[Dict[str, Any]] = []
        for run in self.runs:
            scenario_payload: Dict[str, Any] = {
                "agent": run.blueprint.agent,
                "name": run.blueprint.name,
                "passed": run.result.passed,
                "duration": run.result.duration,
                "max_latency": run.blueprint.thresholds.get("max_latency"),
                "min_context_docs": run.blueprint.thresholds.get("min_context_docs"),
                "min_matches": run.blueprint.thresholds.get("min_matches"),
                "issues": list(run.result.issues),
                "context_documents": run.result.context_documents,
                "context_collections": dict(run.result.context_collections),
                "domain_documents": dict(run.result.domain_documents),
                "knowledge_base": dict(run.result.knowledge_base),
                "response_success": run.result.response.success,
            }
            response_data = run.result.response.data or {}
            if "answer" in response_data:
                scenario_payload["answer"] = response_data.get("answer")
            if "matches" in response_data:
                scenario_payload["match_count"] = len(response_data.get("matches", []))
            scenarios.append(scenario_payload)

        return {"passed": self.passed, "scenarios": scenarios}


def _deep_update(base: MutableMapping[str, Any], updates: Mapping[str, Any]) -> None:
    """Recursively merge ``updates`` into ``base`` preserving nested mappings."""

    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), MutableMapping):
            _deep_update(base[key], value)
        else:
            base[key] = copy.deepcopy(value)


def load_suite_definition(
    overrides: Mapping[str, Any] | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Return the suite definition merging any overrides provided by the caller."""

    definition = copy.deepcopy(DEFAULT_SUITE_DEFINITION)
    if overrides:
        _deep_update(definition, overrides)
    return definition


def _normalise_documents(entries: Sequence[Any]) -> List[tuple[str, str]]:
    normalised: List[tuple[str, str]] = []
    for entry in entries:
        text: Any
        collection: Any
        if isinstance(entry, Mapping):
            text = entry.get("text")
            collection = entry.get("collection", "conversion_rules")
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            text, collection = entry
        else:
            text, collection = entry, "conversion_rules"
        if text is None:
            raise ValueError("Document entries must define text content")
        normalised.append((str(text), str(collection)))
    return normalised


def _count_documents_by_collection(documents: Sequence[tuple[str, str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for _, collection in documents:
        counts[collection] = counts.get(collection, 0) + 1
    return counts


def _normalise_matches(entries: Sequence[Any]) -> List[Dict[str, Any]]:
    normalised: List[Dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            content = entry.get("content")
            metadata = entry.get("metadata", {})
        else:
            content, metadata = entry, {}
        normalised.append({"content": str(content), "metadata": dict(metadata)})
    return normalised


def _extract_task(config: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
    task_config = config.get("task") or {}
    task_type = str(task_config.get("task_type"))
    if not task_type:
        raise ValueError("Each scenario configuration must define a task_type")
    payload = copy.deepcopy(task_config.get("payload", {}))
    return task_type, payload


def _build_document_scenario(name: str, config: Mapping[str, Any]) -> AgentScenario:
    task_type, payload = _extract_task(config)
    documents = _normalise_documents(config.get("documents", []))
    llm_config = config.get("llm", {})
    expected_answer = llm_config.get("answer")
    fragments = [str(fragment) for fragment in llm_config.get("context_fragments", [])]
    thresholds = config.get("thresholds", {})
    max_latency = float(thresholds.get("max_latency", 0.5))
    min_context_docs = thresholds.get("min_context_docs")
    if min_context_docs is None and documents:
        min_context_docs = len(documents)
    expected_collections = config.get("expected_collections")
    if expected_collections is None and documents:
        expected_collections = _count_documents_by_collection(documents)
    expected_domains = config.get("expected_domains")
    quality = config.get("quality", {})
    language = payload.get("language")
    expected_question = str(payload.get("question", "")).strip()
    harness_ref: Dict[str, Any] = {"harness": None}

    def _setup(context: ScenarioContext) -> None:
        context.set_documents(*documents)
        harness_ref["harness"] = context.harness

        def _llm_callback(payload_dict: Dict[str, Any]) -> str:
            assert payload_dict["question"].strip() == expected_question
            if language:
                assert payload_dict.get("language") == language
            context_text = payload_dict.get("context", "")
            assert isinstance(context_text, str)
            assert context_text, "Se esperaba contexto recuperado."
            for fragment in fragments:
                assert fragment in context_text
            if expected_answer is None:
                return ""
            return str(expected_answer)

        context.set_llm_callback(_llm_callback)

    def _quality(response: AgentResponse) -> None:
        metadata = response.metadata or {}
        expected_language = quality.get("language")
        if expected_language:
            assert metadata.get("language") == expected_language
        answer_contains = quality.get("answer_contains") or []
        if answer_contains:
            answer_value = (response.data or {}).get("answer", "")
            for fragment in answer_contains:
                assert fragment in answer_value

    def _query(question: str, language_code: Optional[str]) -> str:
        harness = harness_ref.get("harness")
        if harness is None:
            raise RuntimeError("Harness no inicializado para el escenario documental")

        combined_collections = _count_documents_by_collection(documents)
        harness.last_metrics = {
            "kwargs": {
                "context_documents": len(documents),
                "context_collections": dict(combined_collections),
                "collection_domains": dict(harness.collection_domains),
            }
        }
        harness.context_breakdown = dict(combined_collections)

        simulated_context = "\n".join(text for text, _ in documents)
        callback_payload = {
            "question": question.strip(),
            "context": simulated_context,
            "language": language_code or language,
            "prompt_variant": "documental",
        }
        llm_callback = getattr(harness, "llm_callback", None)
        if callable(llm_callback):
            llm_callback(callback_payload)

        return "" if expected_answer is None else str(expected_answer)

    return AgentScenario(
        name=name,
        agent_factory=lambda: DocumentAgent(query_function=_query),
        task=AgentTask(task_type=task_type, payload=payload),
        setup=_setup,
        expected_success=True,
        expected_answer=str(expected_answer) if expected_answer is not None else None,
        max_latency=max_latency,
        min_context_docs=int(min_context_docs) if min_context_docs is not None else None,
        expected_collections={k: int(v) for k, v in (expected_collections or {}).items()}
        or None,
        expected_domains={k: int(v) for k, v in (expected_domains or {}).items()} or None,
        quality_check=_quality,
    )


def _build_media_scenario(name: str, config: Mapping[str, Any]) -> AgentScenario:
    task_type, payload = _extract_task(config)
    thresholds = config.get("thresholds", {})
    max_latency = float(thresholds.get("max_latency", 0.1))
    quality = config.get("quality", {})
    expected_instructions = [str(value) for value in quality.get("expected_instructions", [])]
    if not expected_instructions:
        instructions = payload.get("instructions")
        if isinstance(instructions, (list, tuple)):
            expected_instructions = [str(value).strip().lower() for value in instructions if str(value).strip()]

    media_reference = payload.get("media")

    def _setup(context: ScenarioContext) -> None:
        context.set_documents()

    def _quality(response: AgentResponse) -> None:
        data = response.data or {}
        metadata = response.metadata or {}
        assert data.get("media") == media_reference
        results = data.get("results") or []
        assert len(results) == len(expected_instructions)
        for item, instruction in zip(results, expected_instructions):
            assert item.get("instruction") == instruction
            assert item.get("status") == "pending"
        if expected_instructions:
            assert metadata.get("instructions") == expected_instructions
        response_type = quality.get("response_type")
        if response_type:
            assert metadata.get("response_type") == response_type

    return AgentScenario(
        name=name,
        agent_factory=lambda: MediaAgent(),
        task=AgentTask(task_type=task_type, payload=payload),
        setup=_setup,
        expected_success=True,
        max_latency=max_latency,
        quality_check=_quality,
    )


def _build_code_scenario(name: str, config: Mapping[str, Any]) -> AgentScenario:
    task_type, payload = _extract_task(config)
    raw_matches = config.get("matches") or []
    matches = _normalise_matches(raw_matches)
    thresholds = config.get("thresholds", {})
    max_latency = float(thresholds.get("max_latency", 0.1))
    min_matches = thresholds.get("min_matches")
    quality = config.get("quality", {})
    expected_collection = quality.get("collection")
    expected_language = quality.get("language")
    snapshot = quality.get("matches_snapshot") or matches
    limit = payload.get("limit")
    if not isinstance(limit, int) or limit <= 0:
        limit = len(matches)

    def _retriever(query: str, requested_limit: int) -> Sequence[Mapping[str, Any]]:
        assert query == str(payload.get("query"))
        final_limit = requested_limit or len(matches)
        sliced = matches[: final_limit]
        return [
            {"content": item["content"], "metadata": dict(item["metadata"])}
            for item in sliced
        ]

    def _setup(_: ScenarioContext) -> None:
        return None

    def _quality(response: AgentResponse) -> None:
        data = response.data or {}
        metadata = response.metadata or {}
        if expected_collection:
            assert data.get("collection") == expected_collection
        if expected_language:
            assert metadata.get("language") == expected_language
        if min_matches is not None:
            assert metadata.get("match_count", 0) >= int(min_matches)
        assert data.get("matches") == snapshot

    agent_factory = lambda: CodeAgent(
        config=CodeAgentConfig(max_results=max(int(limit), 1)),
        retriever=_retriever,
    )

    return AgentScenario(
        name=name,
        agent_factory=agent_factory,
        task=AgentTask(task_type=task_type, payload=payload),
        setup=_setup,
        expected_success=True,
        max_latency=max_latency,
        quality_check=_quality,
    )


def _build_legal_scenario(name: str, config: Mapping[str, Any], module: Any) -> AgentScenario:
    task_type, payload = _extract_task(config)
    documents = _normalise_documents(config.get("documents", []))
    llm_config = config.get("llm", {})
    expected_answer = llm_config.get("answer")
    fragments = [str(fragment) for fragment in llm_config.get("context_fragments", [])]
    thresholds = config.get("thresholds", {})
    max_latency = float(thresholds.get("max_latency", 0.5))
    min_context_docs = thresholds.get("min_context_docs", 1)
    expected_collections = config.get("expected_collections")
    if expected_collections is None and documents:
        expected_collections = _count_documents_by_collection(documents)
    expected_domains = config.get("expected_domains")
    quality = config.get("quality", {})
    language = payload.get("language")
    prompt_variant = quality.get("enforce_prompt_variant", "legal")

    harness_ref: Dict[str, Any] = {"harness": None}

    def _setup(context: ScenarioContext) -> None:
        harness = context.harness
        harness_ref["harness"] = harness
        for _, collection in documents:
            if collection not in harness.collection_domains and "legal" in collection:
                harness.collection_domains[collection] = "legal"
        context.set_documents(*documents)

        def _llm_callback(payload_dict: Dict[str, Any]) -> str:
            variant = quality.get("enforce_prompt_variant")
            if variant:
                assert payload_dict.get("prompt_variant") == variant
            if language:
                assert payload_dict.get("language") == language
            context_text = payload_dict.get("context", "")
            assert isinstance(context_text, str)
            for fragment in fragments:
                assert fragment in context_text
            if expected_answer is None:
                return ""
            return str(expected_answer)

        context.set_llm_callback(_llm_callback)

    def _quality(response: AgentResponse) -> None:
        metadata = response.metadata or {}
        expected_language = quality.get("language")
        if expected_language:
            assert metadata.get("language") == expected_language
        assert response.success

    def _query(question: str, language_code: Optional[str]) -> str:
        harness = harness_ref.get("harness")
        if harness is None:
            raise RuntimeError("Harness no inicializado para el escenario legal")

        combined_collections = _count_documents_by_collection(documents)
        harness.last_metrics = {
            "kwargs": {
                "context_documents": len(documents),
                "context_collections": dict(combined_collections),
                "collection_domains": dict(harness.collection_domains),
            }
        }
        harness.context_breakdown = dict(combined_collections)

        simulated_context = "\n".join(text for text, _ in documents)
        callback_payload = {
            "question": question.strip(),
            "context": simulated_context,
            "language": language_code or language,
            "prompt_variant": prompt_variant,
        }
        llm_callback = getattr(harness, "llm_callback", None)
        if callable(llm_callback):
            llm_callback(callback_payload)

        return "" if expected_answer is None else str(expected_answer)

    return AgentScenario(
        name=name,
        agent_factory=lambda: DocumentAgent(query_function=_query),
        task=AgentTask(task_type=task_type, payload=payload),
        setup=_setup,
        expected_success=True,
        expected_answer=str(expected_answer) if expected_answer is not None else None,
        max_latency=max_latency,
        min_context_docs=int(min_context_docs) if min_context_docs is not None else None,
        expected_collections={k: int(v) for k, v in (expected_collections or {}).items()} or None,
        expected_domains={k: int(v) for k, v in (expected_domains or {}).items()} or None,
        quality_check=_quality,
    )


def build_blueprints(module: Any, definition: Mapping[str, Mapping[str, Any]]) -> List[ScenarioBlueprint]:
    """Create scenario blueprints from the provided suite definition."""

    blueprints: List[ScenarioBlueprint] = []
    for key, config in definition.items():
        agent = str(config.get("agent", key))
        name = str(config.get("name", f"{agent}_{key}"))
        thresholds = dict(config.get("thresholds", {}))
        if agent == "document":
            scenario = _build_document_scenario(name, config)
        elif agent == "media":
            scenario = _build_media_scenario(name, config)
        elif agent == "code":
            scenario = _build_code_scenario(name, config)
        elif agent == "legal":
            scenario = _build_legal_scenario(name, config, module)
        else:
            raise ValueError(f"Unsupported agent type: {agent!r}")
        blueprints.append(ScenarioBlueprint(agent=agent, name=name, thresholds=thresholds, scenario=scenario))
    return blueprints


def run_suite_with(
    module: Any,
    harness: Any,
    overrides: Mapping[str, Any] | None = None,
) -> SuiteReport:
    """Execute the regression suite using the provided module and harness."""

    definition = load_suite_definition(overrides=overrides)
    blueprints = build_blueprints(module, definition)
    regression = AgentRegressionHarness(module, harness)
    results = regression.run([blueprint.scenario for blueprint in blueprints])
    runs = [ScenarioRun(blueprint=blueprint, result=result) for blueprint, result in zip(blueprints, results)]
    return SuiteReport(runs=runs)


def format_text_report(report: SuiteReport) -> str:
    """Return a human readable summary for the regression results."""

    header = (
        f"{'Agente':<10} {'Escenario':<32} {'Estado':<8} {'Latencia(s)':<12} "
        f"{'Umbral':<10} {'Cobertura':<18} Incidencias"
    )
    lines = [header, "-" * len(header)]

    for run in report.runs:
        result = run.result
        thresholds = run.blueprint.thresholds
        status = "OK" if result.passed else "FALLO"
        latency = f"{result.duration:.4f}"
        latency_threshold = thresholds.get("max_latency")
        latency_label = f"≤{latency_threshold}" if latency_threshold is not None else "-"
        context_count = result.context_documents
        context_threshold = thresholds.get("min_context_docs")
        metadata = result.response.metadata or {}
        data = result.response.data or {}
        context_summary: str
        if context_threshold is not None and context_count is not None:
            context_summary = f"{context_count}/{int(context_threshold)} docs"
        elif "min_matches" in thresholds:
            expected_matches = int(thresholds.get("min_matches", 0))
            actual_matches = metadata.get("match_count", len(data.get("matches", [])))
            context_summary = f"{actual_matches}/{expected_matches} coincidencias"
        elif context_count is not None:
            context_summary = f"{context_count} docs"
        else:
            context_summary = "-"
        issues = ", ".join(result.issues) if result.issues else "-"
        lines.append(
            f"{run.blueprint.agent:<10} {run.blueprint.name:<32} {status:<8} "
            f"{latency:<12} {latency_label:<10} {context_summary:<18} {issues}"
        )

    for run in report.runs:
        result = run.result
        lines.append("")
        lines.append(f"[{run.blueprint.agent}] {run.blueprint.name}")
        if result.context_collections:
            lines.append(f"  Colecciones: {result.context_collections}")
        if result.domain_documents:
            lines.append(f"  Dominios: {result.domain_documents}")
        response_data = result.response.data or {}
        if "answer" in response_data:
            answer = str(response_data["answer"])
            lines.append(f"  Respuesta: {answer}")
        if "matches" in response_data:
            lines.append(f"  Coincidencias: {len(response_data['matches'])}")

    return "\n".join(lines)


def load_config_from_path(path: Path) -> Mapping[str, Any]:
    """Load suite overrides from *path* supporting JSON or YAML payloads."""

    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Se proporcionó un archivo YAML pero PyYAML no está instalado."
            ) from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text or "{}")
    if not isinstance(data, Mapping):
        raise ValueError("El archivo de configuración debe contener un mapeo en la raíz.")
    return data


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point used by ``python -m tests.regression.agent_suite``."""

    parser = argparse.ArgumentParser(
        description="Ejecuta el harness de regresión para agentes especializados.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help=(
            "Ruta a un archivo JSON/YAML con overrides de datasets y umbrales. "
            "Si se omite, se usa la variable AGENT_REGRESSION_CONFIG si está definida."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Formato del reporte generado (por defecto texto legible).",
    )

    args = parser.parse_args(argv)
    config_path: Optional[Path]
    if args.config is not None:
        config_path = args.config
    else:
        env_path = os.getenv("AGENT_REGRESSION_CONFIG")
        config_path = Path(env_path) if env_path else None

    overrides: Mapping[str, Any] | None = None
    if config_path is not None:
        overrides = load_config_from_path(config_path)

    module, harness, finalize = build_regression_harness()
    try:
        report = run_suite_with(module, harness, overrides=overrides)
    finally:
        finalize()

    if args.format == "json":
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))

    return 0 if report.passed else 1


def main() -> int:  # pragma: no cover - thin wrapper
    return run_cli()


__all__ = [
    "DEFAULT_SUITE_DEFINITION",
    "ScenarioBlueprint",
    "ScenarioRun",
    "SuiteReport",
    "load_suite_definition",
    "build_blueprints",
    "run_suite_with",
    "format_text_report",
    "load_config_from_path",
    "run_cli",
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

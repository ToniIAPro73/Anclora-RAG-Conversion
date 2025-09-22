"""Observability utilities based on Prometheus metrics."""
from __future__ import annotations

import logging
import os
import threading
from collections import defaultdict
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram, start_http_server
except Exception:  # pragma: no cover - fallback path when dependency is missing
    REGISTRY = None  # type: ignore[assignment]
    Counter = Gauge = Histogram = None  # type: ignore[assignment]
    start_http_server = None  # type: ignore[assignment]


_METRICS_ENABLED = Counter is not None and Histogram is not None and start_http_server is not None
_METRIC_PREFIX = os.getenv("PROMETHEUS_METRIC_PREFIX", "anclora").strip()

_server_lock = threading.Lock()
_server_started = False
_METRIC_CACHE: dict[str, Any] = {}


class _NoopCollector:
    """Fallback collector used when ``prometheus_client`` is unavailable."""

    def labels(self, **_: object) -> "_NoopCollector":  # pragma: no cover - trivial
        return self

    def inc(self, *args: object, **kwargs: object) -> None:  # pragma: no cover - trivial
        return None

    def observe(self, *args: object, **kwargs: object) -> None:  # pragma: no cover - trivial
        return None

    def set(self, *args: object, **kwargs: object) -> None:  # pragma: no cover - trivial
        return None


def _metric_name(name: str) -> str:
    if not _METRIC_PREFIX:
        return name
    return f"{_METRIC_PREFIX}_{name}"


def _get_registered_metric(metric_name: str) -> Any | None:
    """Return a previously created metric instance if it exists."""

    cached = _METRIC_CACHE.get(metric_name)
    if cached is not None:
        return cached

    if not _METRICS_ENABLED or REGISTRY is None:
        return None

    registry = REGISTRY
    try:
        collectors = getattr(registry, "_names_to_collectors")  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - defensive branch
        return None

    collector = collectors.get(metric_name) if isinstance(collectors, Mapping) else None
    if collector is not None:
        _METRIC_CACHE[metric_name] = collector
    return collector


def _build_metric(
    factory,
    name: str,
    documentation: str,
    labelnames: tuple[str, ...] = (),
    buckets: Optional[tuple[float, ...]] = None,
):
    if not _METRICS_ENABLED:
        return _NoopCollector()

    metric_name = _metric_name(name)
    existing = _get_registered_metric(metric_name)
    if existing is not None:
        logger.debug("Reutilizando colector existente para la métrica %s", metric_name)
        return existing

    try:
        if buckets is not None and factory is Histogram:
            metric = factory(metric_name, documentation, labelnames=labelnames, buckets=buckets)
        else:
            metric = factory(metric_name, documentation, labelnames=labelnames)
    except Exception as exc:  # pragma: no cover - defensive branch
        fallback = _get_registered_metric(metric_name)
        if fallback is not None:
            logger.debug(
                "Se reutilizó el colector existente para %s tras una excepción: %s",
                metric_name,
                exc,
            )
            return fallback

        logger.warning("No se pudo crear la métrica %s: %s", metric_name, exc)
        return _NoopCollector()

    _METRIC_CACHE[metric_name] = metric
    return metric


_RAG_REQUESTS = _build_metric(
    Counter,
    "rag_requests_total",
    "Total de consultas RAG procesadas.",
    ("language", "status"),
)
_RAG_LATENCY = _build_metric(
    Histogram,
    "rag_request_latency_seconds",
    "Latencia de respuestas generadas mediante RAG.",
    ("language", "status"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
_RAG_CONTEXT = _build_metric(
    Histogram,
    "rag_context_documents",
    "Número de documentos utilizados como contexto en cada consulta.",
    ("language",),
    buckets=(0, 1, 2, 3, 4, 5, 10, 20, 50, 100),
)
_RAG_COLLECTION_USAGE = _build_metric(
    Counter,
    "rag_collection_usage_total",
    "Consultas RAG en las que participó cada colección.",
    ("collection", "domain", "language", "status"),
)
_RAG_COLLECTION_CONTEXT = _build_metric(
    Histogram,
    "rag_collection_context_documents",
    "Cantidad de documentos aportados por colección en cada respuesta.",
    ("collection", "domain", "language"),
    buckets=(0, 1, 2, 3, 4, 5, 10, 20, 50, 100),
)
_RAG_DOMAIN_USAGE = _build_metric(
    Counter,
    "rag_domain_usage_total",
    "Consultas RAG en las que participó cada dominio de conocimiento.",
    ("domain", "language", "status"),
)
_RAG_DOMAIN_CONTEXT = _build_metric(
    Histogram,
    "rag_domain_context_documents",
    "Documentos utilizados por dominio en el contexto de las respuestas RAG.",
    ("domain", "language"),
    buckets=(0, 1, 2, 3, 4, 5, 10, 20, 50, 100),
)

_AGENT_REQUESTS = _build_metric(
    Counter,
    "agent_requests_total",
    "Total de tareas atendidas por agentes especializados.",
    ("agent", "task_type", "status", "language"),
)
_AGENT_LATENCY = _build_metric(
    Histogram,
    "agent_latency_seconds",
    "Latencia observada al resolver tareas en los agentes.",
    ("agent", "task_type", "status", "language"),
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20),
)

_INGESTION_OPERATIONS = _build_metric(
    Counter,
    "ingestion_operations_total",
    "Operaciones de ingestión de archivos por dominio.",
    ("domain", "extension", "status"),
)
_INGESTION_DURATION = _build_metric(
    Histogram,
    "ingestion_duration_seconds",
    "Duración de los procesos de ingestión de archivos.",
    ("domain", "extension", "status"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
_INGESTION_DOCUMENTS = _build_metric(
    Histogram,
    "ingestion_documents",
    "Cantidad de fragmentos generados a partir de cada archivo.",
    ("domain", "extension", "status"),
    buckets=(0, 1, 2, 5, 10, 20, 50, 100, 200, 500),
)

_ORCHESTRATOR_ROUTING = _build_metric(
    Counter,
    "orchestrator_routing_total",
    "Decisiones de ruteo realizadas por el orquestador multi-agente.",
    ("task_type", "result"),
)

_KNOWLEDGE_BASE_SIZE = _build_metric(
    Gauge,
    "knowledge_base_documents",
    "Cantidad de documentos disponibles en la base de conocimiento por colección.",
    ("collection", "domain"),
)
_KNOWLEDGE_BASE_DOMAIN_SIZE = _build_metric(
    Gauge,
    "knowledge_base_domain_documents",
    "Cantidad total de documentos disponibles por dominio de conocimiento.",
    ("domain",),
)

# Métricas para análisis predictivo
_PREDICTIVE_INSIGHTS = _build_metric(
    Counter,
    "predictive_insights_total",
    "Total de insights predictivos generados por tipo.",
    ("insight_type", "impact_level"),
)
_PREDICTIVE_CONFIDENCE = _build_metric(
    Histogram,
    "predictive_confidence_score",
    "Score de confianza de los insights predictivos.",
    ("insight_type",),
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
_USAGE_PATTERNS = _build_metric(
    Counter,
    "usage_patterns_detected_total",
    "Patrones de uso detectados por tipo.",
    ("pattern_type",),
)
_QUERY_COMPLEXITY = _build_metric(
    Histogram,
    "query_complexity_score",
    "Score de complejidad de las consultas procesadas.",
    ("language",),
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
_USER_SATISFACTION = _build_metric(
    Histogram,
    "user_satisfaction_score",
    "Score de satisfacción del usuario reportado.",
    ("language",),
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

# Métricas para auto-optimización
_OPTIMIZATION_ACTIONS = _build_metric(
    Counter,
    "optimization_actions_total",
    "Acciones de optimización ejecutadas por tipo.",
    ("action_type", "target_component", "status"),
)
_OPTIMIZATION_IMPROVEMENT = _build_metric(
    Histogram,
    "optimization_improvement_score",
    "Score de mejora conseguida por las optimizaciones.",
    ("action_type", "target_component"),
    buckets=(-1.0, -0.5, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0),
)
_OPTIMIZATION_DURATION = _build_metric(
    Histogram,
    "optimization_duration_seconds",
    "Duración de las acciones de optimización.",
    ("action_type", "target_component"),
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
)

# Métricas para seguridad avanzada
_SECURITY_EVENTS = _build_metric(
    Counter,
    "security_events_total",
    "Eventos de seguridad detectados por tipo y nivel de amenaza.",
    ("event_type", "threat_level", "source_type"),
)
_SECURITY_RESPONSE_TIME = _build_metric(
    Histogram,
    "security_response_time_seconds",
    "Tiempo de respuesta a eventos de seguridad.",
    ("event_type", "threat_level"),
    buckets=(0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30),
)
_QUARANTINED_IPS = _build_metric(
    Gauge,
    "quarantined_ips_total",
    "Número total de IPs en cuarentena.",
    (),
)
_BEHAVIORAL_ANOMALIES = _build_metric(
    Counter,
    "behavioral_anomalies_total",
    "Anomalías de comportamiento detectadas por usuario.",
    ("anomaly_type",),
)


def _maybe_start_metrics_server() -> None:
    """Start the Prometheus HTTP server once if requested via environment variables."""

    if not _METRICS_ENABLED:
        return

    port_value = os.getenv("PROMETHEUS_METRICS_PORT")
    if not port_value:
        return

    host = os.getenv("PROMETHEUS_METRICS_HOST", "0.0.0.0")
    try:
        port = int(port_value)
    except ValueError:  # pragma: no cover - invalid configuration
        logger.warning("Valor inválido para PROMETHEUS_METRICS_PORT: %s", port_value)
        return

    global _server_started
    if _server_started:
        return

    with _server_lock:
        if _server_started:
            return
        try:
            start_http_server(port, addr=host)
        except Exception as exc:  # pragma: no cover - defensive branch
            logger.warning("No se pudo iniciar el servidor de métricas en %s:%s (%s)", host, port, exc)
            return
        _server_started = True
        logger.info("Servidor de métricas Prometheus escuchando en %s:%s", host, port)


def _normalise_language(language: Optional[str]) -> str:
    if not language:
        return "unknown"
    return str(language).strip().lower() or "unknown"


def _resolve_domain(
    collection: Optional[str],
    collection_domains: Optional[Mapping[str, str]],
) -> str:
    if not collection:
        return "unknown"
    if not collection_domains:
        return "unknown"
    direct = collection_domains.get(collection)
    if direct:
        return str(direct)
    lowered = collection.lower()
    return str(collection_domains.get(lowered, "unknown"))


def record_rag_response(
    language: Optional[str],
    status: str,
    duration_seconds: Optional[float] = None,
    context_documents: Optional[int] = None,
    collection_documents: Optional[int] = None,
    context_collections: Optional[Mapping[str, int]] = None,
    knowledge_base_collections: Optional[Mapping[str, int]] = None,
    collection_domains: Optional[Mapping[str, str]] = None,
) -> None:
    """Record the outcome of a RAG response pipeline."""

    _maybe_start_metrics_server()
    normalised_language = _normalise_language(language)
    labels = {"language": normalised_language, "status": status}

    _RAG_REQUESTS.labels(**labels).inc()

    if duration_seconds is not None:
        _RAG_LATENCY.labels(**labels).observe(max(float(duration_seconds), 0.0))

    if context_documents is not None:
        _RAG_CONTEXT.labels(language=normalised_language).observe(max(float(context_documents), 0.0))

    if context_collections:
        domain_totals: dict[str, float] = defaultdict(float)
        for collection, count in context_collections.items():
            docs = max(float(count), 0.0)
            collection_label = str(collection).strip() or "unknown"
            domain_label = _resolve_domain(collection_label, collection_domains)
            _RAG_COLLECTION_USAGE.labels(
                collection=collection_label,
                domain=domain_label,
                language=normalised_language,
                status=status,
            ).inc()
            _RAG_COLLECTION_CONTEXT.labels(
                collection=collection_label,
                domain=domain_label,
                language=normalised_language,
            ).observe(docs)
            domain_totals[domain_label] += docs

        for domain_label, docs in domain_totals.items():
            _RAG_DOMAIN_USAGE.labels(
                domain=domain_label,
                language=normalised_language,
                status=status,
            ).inc()
            _RAG_DOMAIN_CONTEXT.labels(
                domain=domain_label,
                language=normalised_language,
            ).observe(docs)

    if knowledge_base_collections:
        per_domain_totals: dict[str, float] = defaultdict(float)
        for collection, count in knowledge_base_collections.items():
            docs = max(float(count), 0.0)
            collection_label = str(collection).strip() or "unknown"
            domain_label = _resolve_domain(collection_label, collection_domains)
            _KNOWLEDGE_BASE_SIZE.labels(collection=collection_label, domain=domain_label).set(docs)
            per_domain_totals[domain_label] += docs

        for domain_label, docs in per_domain_totals.items():
            _KNOWLEDGE_BASE_DOMAIN_SIZE.labels(domain=domain_label).set(docs)
    elif collection_documents is not None:
        _KNOWLEDGE_BASE_SIZE.labels(collection="vectordb", domain="unknown").set(
            max(float(collection_documents), 0.0)
        )

def record_agent_invocation(
    agent_name: str,
    task_type: str,
    status: str,
    duration_seconds: Optional[float] = None,
    language: Optional[str] = None,
) -> None:
    """Record execution metadata for an agent invocation."""

    _maybe_start_metrics_server()
    labels = {
        "agent": agent_name,
        "task_type": task_type,
        "status": status,
        "language": _normalise_language(language),
    }

    _AGENT_REQUESTS.labels(**labels).inc()

    if duration_seconds is not None:
        _AGENT_LATENCY.labels(**labels).observe(max(float(duration_seconds), 0.0))


def record_ingestion(
    domain: str,
    extension: str,
    status: str,
    duration_seconds: Optional[float] = None,
    document_count: Optional[int] = None,
) -> None:
    """Record metrics for a file ingestion operation."""

    _maybe_start_metrics_server()
    labels = {
        "domain": domain,
        "extension": extension or "unknown",
        "status": status,
    }

    _INGESTION_OPERATIONS.labels(**labels).inc()

    if duration_seconds is not None:
        _INGESTION_DURATION.labels(**labels).observe(max(float(duration_seconds), 0.0))

    if document_count is not None:
        _INGESTION_DOCUMENTS.labels(**labels).observe(max(float(document_count), 0.0))


def record_orchestrator_decision(task_type: str, result: str) -> None:
    """Register routing decisions performed by the orchestrator service."""

    _maybe_start_metrics_server()
    _ORCHESTRATOR_ROUTING.labels(task_type=task_type, result=result).inc()


def record_predictive_insight(
    insight_type: str,
    impact_level: str,
    confidence_score: float
) -> None:
    """Record a predictive insight generated by the system."""

    _maybe_start_metrics_server()
    _PREDICTIVE_INSIGHTS.labels(
        insight_type=insight_type,
        impact_level=impact_level
    ).inc()

    _PREDICTIVE_CONFIDENCE.labels(insight_type=insight_type).observe(
        max(0.0, min(1.0, confidence_score))
    )


def record_usage_pattern(pattern_type: str) -> None:
    """Record a usage pattern detected by the system."""

    _maybe_start_metrics_server()
    _USAGE_PATTERNS.labels(pattern_type=pattern_type).inc()


def record_query_metrics(
    language: Optional[str],
    complexity_score: float,
    satisfaction_score: Optional[float] = None
) -> None:
    """Record query-level metrics for analysis."""

    _maybe_start_metrics_server()
    normalised_language = _normalise_language(language)

    _QUERY_COMPLEXITY.labels(language=normalised_language).observe(
        max(0.0, min(1.0, complexity_score))
    )

    if satisfaction_score is not None:
        _USER_SATISFACTION.labels(language=normalised_language).observe(
            max(0.0, min(1.0, satisfaction_score))
        )


def record_optimization_action(
    action_type: str,
    target_component: str,
    status: str,
    improvement_score: Optional[float] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """Record an optimization action executed by the auto-optimizer."""

    _maybe_start_metrics_server()
    _OPTIMIZATION_ACTIONS.labels(
        action_type=action_type,
        target_component=target_component,
        status=status
    ).inc()

    if improvement_score is not None:
        _OPTIMIZATION_IMPROVEMENT.labels(
            action_type=action_type,
            target_component=target_component
        ).observe(improvement_score)

    if duration_seconds is not None:
        _OPTIMIZATION_DURATION.labels(
            action_type=action_type,
            target_component=target_component
        ).observe(max(0.0, duration_seconds))


def record_security_event(
    event_type: str,
    threat_level: str,
    source_type: str = "unknown",
    response_time_seconds: Optional[float] = None
) -> None:
    """Record a security event detected by the advanced security system."""

    _maybe_start_metrics_server()
    _SECURITY_EVENTS.labels(
        event_type=event_type,
        threat_level=threat_level,
        source_type=source_type
    ).inc()

    if response_time_seconds is not None:
        _SECURITY_RESPONSE_TIME.labels(
            event_type=event_type,
            threat_level=threat_level
        ).observe(max(0.0, response_time_seconds))


def record_quarantined_ips(count: int) -> None:
    """Record the current number of quarantined IPs."""

    _maybe_start_metrics_server()
    _QUARANTINED_IPS.set(max(0, count))


def record_behavioral_anomaly(anomaly_type: str) -> None:
    """Record a behavioral anomaly detected."""

    _maybe_start_metrics_server()
    _BEHAVIORAL_ANOMALIES.labels(anomaly_type=anomaly_type).inc()


__all__ = [
    "record_agent_invocation",
    "record_behavioral_anomaly",
    "record_ingestion",
    "record_optimization_action",
    "record_orchestrator_decision",
    "record_predictive_insight",
    "record_quarantined_ips",
    "record_query_metrics",
    "record_rag_response",
    "record_security_event",
    "record_usage_pattern",
]

"""Observability utilities based on Prometheus metrics."""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
except Exception:  # pragma: no cover - fallback path when dependency is missing
    Counter = Gauge = Histogram = None  # type: ignore[assignment]
    start_http_server = None  # type: ignore[assignment]


_METRICS_ENABLED = Counter is not None and Histogram is not None and start_http_server is not None
_METRIC_PREFIX = os.getenv("PROMETHEUS_METRIC_PREFIX", "anclora").strip()

_server_lock = threading.Lock()
_server_started = False


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


def _build_metric(factory, name: str, documentation: str, labelnames: tuple[str, ...] = (), buckets: Optional[tuple[float, ...]] = None):
    if not _METRICS_ENABLED:
        return _NoopCollector()

    metric_name = _metric_name(name)
    try:
        if buckets is not None and factory is Histogram:
            return factory(metric_name, documentation, labelnames=labelnames, buckets=buckets)
        return factory(metric_name, documentation, labelnames=labelnames)
    except Exception as exc:  # pragma: no cover - defensive branch
        logger.warning("No se pudo crear la métrica %s: %s", metric_name, exc)
        return _NoopCollector()


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
    ("collection",),
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


def record_rag_response(
    language: Optional[str],
    status: str,
    duration_seconds: Optional[float] = None,
    context_documents: Optional[int] = None,
    collection_documents: Optional[int] = None,
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

    if collection_documents is not None:
        _KNOWLEDGE_BASE_SIZE.labels(collection="vectordb").set(max(float(collection_documents), 0.0))


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


__all__ = [
    "record_agent_invocation",
    "record_ingestion",
    "record_orchestrator_decision",
    "record_rag_response",
]

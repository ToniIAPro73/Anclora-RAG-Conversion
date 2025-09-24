"""Shared application constants."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Mapping

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

_DEFAULT_CHROMA_HOST = "localhost"
_DEFAULT_CHROMA_PORT = 8000


def _get_chroma_host() -> str:
    """Return the configured Chroma host or the default value."""

    host = os.getenv("CHROMA_HOST", _DEFAULT_CHROMA_HOST).strip()
    if not host:
        logger.warning(
            "Se recibió un valor vacío para CHROMA_HOST. Se utilizará el valor por defecto '%s'.",
            _DEFAULT_CHROMA_HOST,
        )
        return _DEFAULT_CHROMA_HOST
    return host


def _get_chroma_port() -> int:
    """Return the configured Chroma port as an integer, with fallbacks."""

    raw_port = os.getenv("CHROMA_PORT")
    if raw_port is None:
        return _DEFAULT_CHROMA_PORT

    try:
        port = int(raw_port)
    except (TypeError, ValueError):  # pragma: no cover - defensive path
        logger.warning(
            "No fue posible interpretar el valor '%s' de CHROMA_PORT. Se utilizará el valor por defecto %s.",
            raw_port,
            _DEFAULT_CHROMA_PORT,
        )
        return _DEFAULT_CHROMA_PORT

    if port <= 0:  # pragma: no cover - defensive path
        logger.warning(
            "El valor de CHROMA_PORT debe ser positivo. Se recibió '%s'. Se utilizará el valor por defecto %s.",
            raw_port,
            _DEFAULT_CHROMA_PORT,
        )
        return _DEFAULT_CHROMA_PORT

    return port


@dataclass(frozen=True)
class CollectionConfig:
    """Metadata describing a Chroma collection."""

    domain: str
    description: str
    prompt_type: str = "documental"


CHROMA_COLLECTIONS: Mapping[str, CollectionConfig] = {
    "conversion_rules": CollectionConfig(
        domain="documents",
        description=(
            "Colección orientada a manuales, guías y documentación de referencia "
            "utilizada durante los procesos de conversión y capacitación."
        ),
        prompt_type="documental",
    ),
    "troubleshooting": CollectionConfig(
        domain="code",
        description=(
            "Snippets de código, ejemplos y procedimientos de diagnóstico para "
            "dar soporte en escenarios de troubleshooting."
        ),
        prompt_type="documental",
    ),
    "legal_compliance": CollectionConfig(
        domain="legal",
        description=(
            "Políticas legales, lineamientos regulatorios y criterios de cumplimiento "
            "que requieren controles adicionales antes de compartirse."
        ),
    ),
    "multimedia_assets": CollectionConfig(
        domain="multimedia",
        description=(
            "Material audiovisual transcrito como subtítulos o descripciones "
            "para enriquecer respuestas con contenido multimedia."
        ),
        prompt_type="multimedia",
    ),
    "legal_repository": CollectionConfig(
        domain="legal",
        description=(
            "Cuerpos normativos, cláusulas y lineamientos de cumplimiento para "
            "responder consultas legales o regulatorias."
        ),
        prompt_type="legal",
    ),
    "format_specs": CollectionConfig(
        domain="formats",
        description=(
            "Catálogo de convenciones y requisitos de formatos para asegurar "
            "consistencias en entregables y conversiones."
        ),
    ),
    "knowledge_guides": CollectionConfig(
        domain="guides",
        description=(
            "Guías operativas y playbooks paso a paso que estructuran las "
            "respuestas de los agentes con mejores prácticas."
        ),
    ),
    "compliance_archive": CollectionConfig(
        domain="compliance",
        description=(
            "Repositorio de lineamientos regulatorios y políticas internas "
            "para respaldar respuestas con enfoque legal y normativo."
        ),
    ),
}

DOMAIN_TO_COLLECTION: Mapping[str, str] = {
    config.domain: name for name, config in CHROMA_COLLECTIONS.items()
}


def _create_chroma_client() -> chromadb.api.ClientAPI:
    """Create a ChromaDB client, falling back to an in-memory instance if remote access fails."""

    host = _get_chroma_host()
    port = _get_chroma_port()
    settings = Settings(allow_reset=True, anonymized_telemetry=False)

    try:
        return chromadb.HttpClient(
            host=host,
            port=port,
            settings=settings,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning(
            "No fue posible conectar con el servicio remoto de ChromaDB en %s:%s (%s). Se usará un cliente en memoria.",
            host,
            port,
            exc,
        )
        local_settings = Settings(
            allow_reset=True,
            anonymized_telemetry=False,
            is_persistent=False,
        )
        return chromadb.EphemeralClient(settings=local_settings)


CHROMA_SETTINGS = _create_chroma_client()

__all__ = [
    "CHROMA_COLLECTIONS",
    "CHROMA_SETTINGS",
    "CollectionConfig",
    "DOMAIN_TO_COLLECTION",
]

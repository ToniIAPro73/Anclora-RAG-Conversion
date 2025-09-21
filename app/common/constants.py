"""Shared application constants."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionConfig:
    """Metadata describing a Chroma collection."""

    domain: str
    description: str


CHROMA_COLLECTIONS: Mapping[str, CollectionConfig] = {
    "conversion_rules": CollectionConfig(
        domain="documents",
        description=(
            "Colección orientada a manuales, guías y documentación de referencia "
            "utilizada durante los procesos de conversión y capacitación."
        ),
    ),
    "troubleshooting": CollectionConfig(
        domain="code",
        description=(
            "Snippets de código, ejemplos y procedimientos de diagnóstico para "
            "dar soporte en escenarios de troubleshooting."
        ),
    ),
    "multimedia_assets": CollectionConfig(
        domain="multimedia",
        description=(
            "Material audiovisual transcrito como subtítulos o descripciones "
            "para enriquecer respuestas con contenido multimedia."
        ),
    ),
}

DOMAIN_TO_COLLECTION: Mapping[str, str] = {
    config.domain: name for name, config in CHROMA_COLLECTIONS.items()
}


def _create_chroma_client() -> chromadb.api.ClientAPI:
    """Create a ChromaDB client, falling back to an in-memory instance if remote access fails."""

    settings = Settings(allow_reset=True, anonymized_telemetry=False)

    try:
        return chromadb.HttpClient(
            host="host.docker.internal",
            port=8000,
            settings=settings,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning(
            "No fue posible conectar con el servicio remoto de ChromaDB (%s). Se usará un cliente en memoria.",
            exc,
        )
        local_settings = Settings(
            allow_reset=True,
            anonymized_telemetry=False,
            is_persistent=True,
        )
        return chromadb.PersistentClient(path=":memory:", settings=local_settings)


CHROMA_SETTINGS = _create_chroma_client()

__all__ = [
    "CHROMA_COLLECTIONS",
    "CHROMA_SETTINGS",
    "CollectionConfig",
    "DOMAIN_TO_COLLECTION",
]

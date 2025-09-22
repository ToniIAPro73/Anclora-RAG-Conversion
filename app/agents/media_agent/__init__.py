"""Agente responsable de tareas básicas sobre contenidos multimedia."""

from .agent import MediaAgent
from .ingestor import (
    MULTIMEDIA_COLLECTION,
    MultimediaIngestor,
    create_multimedia_ingestor,
)

__all__ = [
    "MULTIMEDIA_COLLECTION",
    "MediaAgent",
    "MultimediaIngestor",
    "create_multimedia_ingestor",
]

"""Archive agent for processing compressed files."""

from .agent import ArchiveAgent
from .ingestor import ARCHIVE_COLLECTION, ArchiveIngestor, create_archive_ingestor

__all__ = [
    "ArchiveAgent",
    "ARCHIVE_COLLECTION", 
    "ArchiveIngestor",
    "create_archive_ingestor",
]

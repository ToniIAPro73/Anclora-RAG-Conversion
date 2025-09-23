"""Domain specific ingestion helpers and agent factories."""

from .base import AgentResponse, AgentTask, BaseAgent, BaseFileIngestor, LoaderConfig
from .code_agent import CODE_COLLECTION, CodeIngestor, create_code_ingestor
from .document_agent import (
    DOCUMENTS_COLLECTION,
    DocumentAgent,
    DocumentIngestor,
    EmailFallbackLoader,
    create_document_ingestor,
    refresh_document_loaders,
)
from .media_agent import (
    MULTIMEDIA_COLLECTION,
    MediaAgent,
    MultimediaIngestor,
    create_multimedia_ingestor,
)
from .archive_agent import (
    ARCHIVE_COLLECTION,
    ArchiveAgent,
    ArchiveIngestor,
    create_archive_ingestor,
)
from .content_analyzer_agent import ContentAnalyzerAgent, ContentAnalysis
from .smart_converter_agent import SmartConverterAgent, ConversionResult
from .orchestrator import OrchestratorService, create_default_orchestrator, document_query_flow

__all__ = [
    "AgentResponse",
    "AgentTask",
    "BaseAgent",
    "BaseFileIngestor",
    "CODE_COLLECTION",
    "CodeIngestor",
    "ContentAnalyzerAgent",
    "ContentAnalysis",
    "ConversionResult",
    "DOCUMENTS_COLLECTION",
    "DocumentAgent",
    "DocumentIngestor",
    "EmailFallbackLoader",
    "LoaderConfig",
    "MULTIMEDIA_COLLECTION",
    "MediaAgent",
    "MultimediaIngestor",
    "ARCHIVE_COLLECTION",
    "ArchiveAgent",
    "ArchiveIngestor",
    "OrchestratorService",
    "SmartConverterAgent",
    "create_code_ingestor",
    "create_default_orchestrator",
    "create_document_ingestor",
    "create_multimedia_ingestor",
    "create_archive_ingestor",
    "document_query_flow",
    "refresh_document_loaders",
]

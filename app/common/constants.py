import os, sys, types
from dataclasses import dataclass
from pathlib import Path

# --- Apagar telemetría ANTES de importar chromadb ---
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"  # compat

# (Cinturón) Stub si alguna lib intenta enviar telemetría
_stub = types.ModuleType("analytics")
def _noop(*_a, **_k): pass
_stub.capture = _noop  # type: ignore[attr-defined]
_stub.track = _noop    # type: ignore[attr-defined]
_stub.identify = _noop # type: ignore[attr-defined]
sys.modules.setdefault("analytics", _stub)
sys.modules.setdefault("posthog", _stub)

# ChromaDB (local, sin server HTTP)
try:
    import chromadb
except ImportError:
    CHROMA_CLIENT = None
else:
    CHROMA_DIR = Path(__file__).resolve().parents[2] / "data" / "chroma"
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    # 0.5.x: usar PersistentClient con path; no pasar Settings aquí
    CHROMA_CLIENT = chromadb.PersistentClient(path=str(CHROMA_DIR))

# ChromaDB Collections with domain information

@dataclass(frozen=True)
class CollectionConfig:
    domain: str

CHROMA_COLLECTIONS = {
    "conversion_rules": CollectionConfig(domain="documents"),
    "technical_docs": CollectionConfig(domain="documents"),
    "business_docs": CollectionConfig(domain="documents"),
    "general_knowledge": CollectionConfig(domain="documents"),
    "research_papers": CollectionConfig(domain="documents"),
    "research_sources": CollectionConfig(domain="research"),
    "knowledge_guides": CollectionConfig(domain="guides"),
    "format_specs": CollectionConfig(domain="formats"),
    "troubleshooting": CollectionConfig(domain="code"),
    "multimedia_assets": CollectionConfig(domain="multimedia"),
    "archive_documents": CollectionConfig(domain="archives"),
    "compliance_archive": CollectionConfig(domain="compliance"),
    "legal_documents": CollectionConfig(domain="legal"),
    "legal_repository": CollectionConfig(domain="legal"),
    "legal_compliance": CollectionConfig(domain="compliance"),
}

DOMAIN_TO_COLLECTION = {
    "documents": "conversion_rules",
    "code": "troubleshooting",
    "multimedia": "multimedia_assets",
    "archives": "archive_documents",
    "research": "research_sources",
    "guides": "knowledge_guides",
    "formats": "format_specs",
    "compliance": "compliance_archive",
    "legal": "legal_documents",
    "business": "business_docs",
}


# Supported file formats
SUPPORTED_FORMATS = {
    "documents": [".pdf", ".docx", ".doc", ".txt", ".md", ".html"],
    "spreadsheets": [".xlsx", ".xls", ".csv"],
    "presentations": [".pptx", ".ppt"],
    "data": [".json", ".xml", ".yaml", ".yml"],
    "archives": [".zip", ".rar"]
}

# API Configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True
}

# Embedding models
EMBEDDING_MODELS = {
    "default": "all-MiniLM-L6-v2",
    "large": "all-mpnet-base-v2"
}

# Chunking configuration
CHUNKING_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200
}

# Processing limits
PROCESSING_LIMITS = {
    "max_file_size_mb": 50,
    "max_files_per_batch": 100,
    "max_concurrent_operations": 10
}

# Validation rules
VALIDATION_RULES = {
    "min_file_size_kb": 1,
    "max_file_size_mb": 50,
    "allowed_characters": "utf-8",
    "max_filename_length": 255
}

# Error messages
ERROR_MESSAGES = {
    "file_too_large": "El archivo excede el tamaño máximo permitido (50MB)",
    "invalid_format": "Formato de archivo no soportado",
    "empty_file": "El archivo está vacío",
    "corrupted_file": "El archivo parece estar corrupto"
}

# Success messages
SUCCESS_MESSAGES = {
    "file_processed": "Archivo procesado exitosamente",
    "batch_completed": "Lote de archivos procesado exitosamente",
    "conversion_success": "Conversión completada exitosamente"
}

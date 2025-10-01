import logging
import os
import sys
import types
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

logger = logging.getLogger(__name__)

# ChromaDB client selection (local persistent by default, HTTP when configured)
try:
    import chromadb
except ImportError:
    CHROMA_CLIENT = None
    CHROMA_DIR = None
else:
    def _is_truthy(value: str | None) -> bool:
        if value is None:
            return False
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _resolve_persist_dir(path_value: str | None) -> Path:
        base_dir = Path(__file__).resolve().parents[2]
        if not path_value:
            resolved = base_dir / "data" / "chroma"
        else:
            candidate = Path(path_value)
            resolved = candidate if candidate.is_absolute() else (base_dir / candidate).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def _build_http_client() -> object | None:
        host = os.environ.get("CHROMA_HOST")
        url = os.environ.get("CHROMA_HTTP_URL") or os.environ.get("CHROMA_SERVER_URL")
        port_value = os.environ.get("CHROMA_PORT")
        ssl_value = os.environ.get("CHROMA_SSL") or os.environ.get("CHROMA_USE_SSL")

        if url and not host:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.hostname or host
            if parsed.port and not port_value:
                port_value = str(parsed.port)
            if parsed.scheme and not ssl_value:
                ssl_value = "true" if parsed.scheme.lower() == "https" else "false"

        if not host:
            return None

        try:
            port = int(port_value) if port_value else 8000
        except ValueError:
            port = 8000

        ssl_enabled = _is_truthy(ssl_value)
        headers: dict[str, str] = {}
        auth_token = os.environ.get("CHROMA_HTTP_AUTH_TOKEN") or os.environ.get("CHROMA_AUTH_TOKEN")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        client_kwargs: dict[str, object] = {
            "host": host,
            "port": port,
            "ssl": ssl_enabled,
        }
        if headers:
            client_kwargs["headers"] = headers

        return chromadb.HttpClient(**client_kwargs)

    client = None
    try:
        client = _build_http_client()
    except Exception as exc:
        logger.warning("Falling back to local Chroma client: %s", exc)
        client = None

    if client is not None:
        CHROMA_CLIENT = client
        CHROMA_DIR = None
    else:
        CHROMA_DIR = _resolve_persist_dir(os.environ.get("CHROMA_PERSIST_DIR"))
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

# --- Backwards compatibility shim ---
CHROMA_SETTINGS = CHROMA_CLIENT  # alias temporal para módulos antiguos
def get_chroma_client():
    return CHROMA_CLIENT


import os

# Disable Chroma telemetry before importing the client stack
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY'] = 'False'

"""Constants for Anclora RAG application"""

try:
    from chromadb.telemetry import telemetry
    telemetry.DEFAULT_CHROMA_TELEMETRY = False
except Exception:
    pass

try:
    from chromadb.telemetry.product import posthog as _chroma_posthog
except Exception:
    _chroma_posthog = None
else:
    def _noop_capture(*_args, **_kwargs):
        return None
    class _SilentPosthog:
        def __init__(self, *args, **kwargs):
            pass
        def capture(self, *_args, **_kwargs):
            return None
        def flush(self) -> None:
            return None
        def dependencies(self):
            return []
        def start(self):
            return None
        def stop(self):
            return None
    _chroma_posthog.capture = _noop_capture
    _chroma_posthog.client = _SilentPosthog()
    _chroma_posthog.Posthog = lambda *args, **kwargs: _SilentPosthog(*args, **kwargs)

# ChromaDB Settings
try:
    import chromadb
    import chromadb.config

    # Get ChromaDB configuration from environment variables
    chroma_host = os.getenv('CHROMA_HOST', 'localhost')
    chroma_port = int(os.getenv('CHROMA_PORT', '8000'))

    settings = chromadb.config.Settings(
        allow_reset=True,
        anonymized_telemetry=False,
    )

    try:
        CHROMA_SETTINGS = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=settings,
        )
    except Exception:
        CHROMA_SETTINGS = chromadb.EphemeralClient(settings=settings)
except ImportError:
    # Fallback for when chromadb is not available
    CHROMA_SETTINGS = None

# ChromaDB Collections with domain information
CHROMA_COLLECTIONS = {
    "general_knowledge": type('CollectionConfig', (), {'domain': 'documents'})(),
    "technical_docs": type('CollectionConfig', (), {'domain': 'documents'})(),
    "business_docs": type('CollectionConfig', (), {'domain': 'documents'})(),
    "research_papers": type('CollectionConfig', (), {'domain': 'documents'})(),
    "legal_documents": type('CollectionConfig', (), {'domain': 'documents'})()
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

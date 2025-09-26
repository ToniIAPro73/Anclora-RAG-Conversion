"""Constants for Anclora RAG application"""

# ChromaDB Collections
CHROMA_COLLECTIONS = [
    "general_knowledge",
    "technical_docs", 
    "business_docs",
    "research_papers",
    "legal_documents"
]

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

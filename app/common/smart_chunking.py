"""
Sistema de chunking inteligente para diferentes tipos de contenido.
Optimizado especialmente para código y documentación técnica.
"""

from typing import List, Dict, Any, Optional
import re
from pathlib import Path

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import TextLoader
    from langchain_core.documents import Document
except ImportError:
    # Fallback para entornos sin langchain
    class _FallbackRecursiveCharacterTextSplitter:
        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 0, separators: Optional[List[str]] = None):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators or ["\n\n", "\n", " "]

        def split_text(self, text: str) -> List[str]:
            # Implementación básica de fallback
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

    class _FallbackDocument:
        def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
            self.page_content = page_content
            self.metadata = metadata or {}

    # Use fallback classes as the main classes when imports fail
    RecursiveCharacterTextSplitter = _FallbackRecursiveCharacterTextSplitter  # type: ignore
    Document = _FallbackDocument  # type: ignore

class SmartChunker:
    """Chunker inteligente que adapta la estrategia según el tipo de contenido"""
    
    # Configuraciones por tipo de contenido
    CHUNKING_CONFIGS = {
        "code": {
            "chunk_size": 1200,
            "chunk_overlap": 100,
            "separators": [
                "\n\nclass ",
                "\n\ndef ",
                "\n\nfunction ",
                "\n\nasync def ",
                "\n\n@",  # decoradores
                "\n\n# ",  # comentarios principales
                "\n\n// ",  # comentarios JS
                "\n\n/*",  # comentarios bloque
                "\n\n",
                "\n",
                " "
            ]
        },
        "documentation": {
            "chunk_size": 800,
            "chunk_overlap": 80,
            "separators": [
                "\n\n## ",
                "\n\n### ",
                "\n\n#### ",
                "\n\n**",  # texto en negrita
                "\n\n- ",  # listas
                "\n\n1. ",  # listas numeradas
                "\n\n",
                "\n",
                ". ",
                " "
            ]
        },
        "mixed": {
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "separators": [
                "\n\n```",  # bloques de código
                "\n\nclass ",
                "\n\ndef ",
                "\n\n## ",
                "\n\n### ",
                "\n\n",
                "\n",
                " "
            ]
        },
        "sql": {
            "chunk_size": 1500,
            "chunk_overlap": 150,
            "separators": [
                "\n\nCREATE ",
                "\n\nALTER ",
                "\n\nSELECT ",
                "\n\nINSERT ",
                "\n\nUPDATE ",
                "\n\nDELETE ",
                "\n\nWITH ",
                "\n\n-- ",
                "\n\n",
                "\n",
                " "
            ]
        }
    }
    
    # Extensiones de archivo por tipo
    FILE_TYPE_MAPPING = {
        # Código
        ".py": "code",
        ".js": "code", 
        ".ts": "code",
        ".java": "code",
        ".cpp": "code",
        ".c": "code",
        ".cs": "code",
        ".go": "code",
        ".rs": "code",
        ".rb": "code",
        ".php": "code",
        ".swift": "code",
        ".kotlin": "code",
        ".scala": "code",
        ".r": "code",
        ".lua": "code",
        ".dart": "code",
        
        # SQL
        ".sql": "sql",
        ".plsql": "sql",
        ".psql": "sql",
        ".mysql": "sql",
        
        # Documentación
        ".md": "documentation",
        ".rst": "documentation",
        ".txt": "mixed",
        ".html": "mixed",
        
        # Por defecto
        "default": "mixed"
    }
    
    def __init__(self):
        self.splitters = {}
        self._initialize_splitters()
    
    def _initialize_splitters(self):
        """Inicializa los splitters para cada tipo de contenido"""
        for content_type, config in self.CHUNKING_CONFIGS.items():
            self.splitters[content_type] = RecursiveCharacterTextSplitter(
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"],
                separators=config["separators"]
            )
    
    def detect_content_type(self, file_path: str, content: Optional[str] = None) -> str:
        """Detecta el tipo de contenido basado en la extensión y contenido"""
        
        # Primero, usar la extensión del archivo
        file_ext = Path(file_path).suffix.lower()
        content_type = self.FILE_TYPE_MAPPING.get(file_ext, "mixed")
        
        # Si tenemos contenido, hacer detección más inteligente
        if content:
            content_lower = content.lower()
            
            # Detectar si es documentación técnica con código
            code_blocks = len(re.findall(r'```\w*\n', content))
            markdown_headers = len(re.findall(r'\n#{1,6}\s', content))
            
            if code_blocks > 2 and markdown_headers > 3:
                content_type = "mixed"
            
            # Detectar SQL puro
            sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'alter']
            sql_count = sum(1 for keyword in sql_keywords if keyword in content_lower)
            
            if sql_count >= 3 and file_ext not in ['.py', '.js', '.java']:
                content_type = "sql"
        
        return content_type
    
    def chunk_content(self, content: str, file_path: str = "", metadata: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Divide el contenido en chunks inteligentes"""
        
        # Detectar tipo de contenido
        content_type = self.detect_content_type(file_path, content)
        
        # Obtener el splitter apropiado
        splitter = self.splitters.get(content_type, self.splitters["mixed"])
        
        # Dividir el contenido
        chunks = splitter.split_text(content)
        
        # Crear documentos con metadatos enriquecidos
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "source": file_path,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "content_type": content_type,
                "chunk_size": len(chunk),
                "language": self._detect_language(file_path, chunk),
                **(metadata or {})
            }
            
            # Agregar metadatos específicos del código
            if content_type == "code":
                chunk_metadata.update(self._extract_code_metadata(chunk, file_path))
            
            documents.append(Document(
                page_content=chunk,
                metadata=chunk_metadata
            ))
        
        return documents
    
    def _detect_language(self, file_path: str, content: str) -> str:
        """Detecta el lenguaje de programación"""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".sql": "sql",
            ".md": "markdown",
            ".html": "html"
        }
        
        return language_map.get(ext, "text")
    
    def _extract_code_metadata(self, chunk: str, file_path: str) -> Dict[str, Any]:
        """Extrae metadatos específicos del código"""
        metadata = {}
        
        # Detectar funciones
        functions = re.findall(r'def\s+(\w+)\s*\(', chunk)  # Python
        functions.extend(re.findall(r'function\s+(\w+)\s*\(', chunk))  # JavaScript
        functions.extend(re.findall(r'public\s+\w+\s+(\w+)\s*\(', chunk))  # Java
        
        if functions:
            metadata["functions"] = functions
            metadata["has_functions"] = True
        
        # Detectar clases
        classes = re.findall(r'class\s+(\w+)', chunk)
        if classes:
            metadata["classes"] = classes
            metadata["has_classes"] = True
        
        # Detectar imports
        imports = re.findall(r'(?:import|from)\s+[\w.]+', chunk)
        if imports:
            metadata["has_imports"] = True
            metadata["import_count"] = len(imports)
        
        # Detectar comentarios
        comment_lines = len(re.findall(r'^\s*#.*$', chunk, re.MULTILINE))  # Python
        comment_lines += len(re.findall(r'^\s*//.*$', chunk, re.MULTILINE))  # JS/Java
        
        if comment_lines > 0:
            metadata["comment_lines"] = comment_lines
            metadata["has_comments"] = True
        
        return metadata
    
    def get_chunking_stats(self, documents: List[Any]) -> Dict[str, Any]:
        """Obtiene estadísticas del chunking realizado"""
        if not documents:
            return {}
        
        chunk_sizes = [len(doc.page_content) for doc in documents]
        content_types = [doc.metadata.get("content_type", "unknown") for doc in documents]
        
        stats = {
            "total_chunks": len(documents),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "content_types": {ct: content_types.count(ct) for ct in set(content_types)},
            "total_characters": sum(chunk_sizes)
        }
        
        return stats

# Instancia global del chunker inteligente
smart_chunker = SmartChunker()

def get_smart_chunker() -> SmartChunker:
    """Obtiene la instancia del chunker inteligente"""
    return smart_chunker

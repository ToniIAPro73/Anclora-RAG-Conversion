# Sistema de Ingesta Avanzado para Anclora RAG

## 📁 Estructura de Archivos del Sistema

```
app/
├── ingestion/
│   ├── __init__.py
│   ├── advanced_ingestion_system.py
│   ├── file_processor.py
│   ├── folder_processor.py
│   ├── markdown_source_parser.py
│   ├── validation_service.py
│   └── config.py
├── pages/
│   └── 02_📤_Ingesta_Avanzada.py
└── components/
    └── ingestion_ui_components.py
```

## 1. Sistema Principal de Ingesta

### `app/ingestion/advanced_ingestion_system.py`

```python
"""
Sistema de Ingesta Avanzado para Anclora RAG
Gestión unificada de archivos individuales, carpetas y markdown estructurado
"""

import os
import asyncio
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from enum import Enum

from .file_processor import FileProcessor
from .folder_processor import FolderProcessor
from .markdown_source_parser import MarkdownSourceParser
from .validation_service import ValidationService
from app.common.logger import Logger
from app.common.config import Config
from app.agents.orchestrator.service import OrchestratorService
from app.orchestration.hybrid_orchestrator import HybridOrchestrator

logger = Logger(__name__)

class IngestionStatus(Enum):
    """Estados posibles del proceso de ingesta"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

@dataclass
class IngestionJob:
    """Representa un trabajo de ingesta"""
    job_id: str
    type: str  # 'file', 'folder', 'markdown_sources'
    status: IngestionStatus = IngestionStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AdvancedIngestionSystem:
    """
    Sistema principal de ingesta con capacidades avanzadas
    """
    
    def __init__(self):
        """Inicializa el sistema de ingesta avanzado"""
        self.config = Config()
        self.file_processor = FileProcessor()
        self.folder_processor = FolderProcessor()
        self.markdown_parser = MarkdownSourceParser()
        self.validator = ValidationService()
        self.orchestrator = HybridOrchestrator()
        self.agent_orchestrator = OrchestratorService()
        
        # Estado del sistema
        self.active_jobs: Dict[str, IngestionJob] = {}
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent_jobs = 5
        self.max_file_size = 200 * 1024 * 1024  # 200MB
        
        # Formatos soportados
        self.supported_formats = {
            'documents': ['.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.odt'],
            'presentations': ['.pptx', '.ppt', '.odp'],
            'spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'code': ['.py', '.js', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.kt', '.swift'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'multimedia': ['.mp3', '.mp4', '.wav', '.avi', '.mov', '.mkv'],
            'markup': ['.html', '.xml', '.json', '.yaml', '.yml']
        }
        
        logger.info("Sistema de Ingesta Avanzado inicializado")
    
    async def ingest_files(
        self,
        files: List[Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionJob:
        """
        Procesa múltiples archivos individuales
        
        Args:
            files: Lista de archivos a procesar
            user_id: ID del usuario
            metadata: Metadata adicional opcional
            
        Returns:
            IngestionJob con el estado del proceso
        """
        job_id = self._generate_job_id(user_id)
        job = IngestionJob(
            job_id=job_id,
            type='file',
            total_files=len(files),
            metadata=metadata or {}
        )
        
        self.active_jobs[job_id] = job
        
        try:
            job.status = IngestionStatus.VALIDATING
            
            # Validar todos los archivos
            valid_files = []
            for file in files:
                validation_result = await self.validator.validate_file(
                    file, 
                    self.max_file_size,
                    self.supported_formats
                )
                
                if validation_result['valid']:
                    valid_files.append({
                        'file': file,
                        'validation': validation_result
                    })
                else:
                    job.errors.append({
                        'file': file.name if hasattr(file, 'name') else str(file),
                        'error': validation_result['error']
                    })
                    job.failed_files += 1
            
            # Procesar archivos válidos
            job.status = IngestionStatus.PROCESSING
            
            for file_info in valid_files:
                try:
                    result = await self._process_single_file(
                        file_info['file'],
                        user_id,
                        file_info['validation']
                    )
                    
                    job.files.append(result)
                    job.processed_files += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando archivo: {e}")
                    job.errors.append({
                        'file': file_info['file'].name,
                        'error': str(e)
                    })
                    job.failed_files += 1
            
            # Actualizar estado final
            if job.processed_files == job.total_files:
                job.status = IngestionStatus.COMPLETED
            elif job.processed_files > 0:
                job.status = IngestionStatus.PARTIALLY_COMPLETED
            else:
                job.status = IngestionStatus.FAILED
                
        except Exception as e:
            logger.error(f"Error en ingesta de archivos: {e}")
            job.status = IngestionStatus.FAILED
            job.errors.append({
                'general': str(e)
            })
        
        finally:
            job.end_time = datetime.now()

        return job

### Formato de `job.files`

Cada elemento agregado a `job.files` incluye un resumen serializable en la clave `summary` para evitar exponer objetos complejos como `ProcessResult`. Este resumen contiene:

- `collection`: nombre de la colección en Chroma asociada al archivo ingerido.
- `domain`: dominio que determinó el esquema de chunking aplicado.
- `chunk_count`: cantidad total de chunks generados durante la normalización.
- `total_characters`: suma de caracteres en todos los chunks procesados.
- `duplicate`: indicador booleano que permite detectar rápidamente si el archivo fue descartado por estar repetido.
- `warnings`: lista opcional de advertencias recogidas durante la conversión (p. ej., problemas puntuales de formato).

Los integradores que necesiten detalles adicionales pueden consultar el mensaje principal (`message`) y la metadata complementaria disponible en el payload del archivo. Si se requiere reconstruir el resultado completo, es posible reingestar el archivo utilizando los helpers tradicionales del módulo `ingest_file`, que continúan devolviendo `ProcessResult` en memoria antes de su serialización.
    
    async def ingest_folder(
        self,
        folder_path: str,
        user_id: str,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionJob:
        """
        Procesa todos los archivos válidos en una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            user_id: ID del usuario
            recursive: Si procesar subcarpetas
            metadata: Metadata adicional
            
        Returns:
            IngestionJob con el estado del proceso
        """
        job_id = self._generate_job_id(user_id)
        job = IngestionJob(
            job_id=job_id,
            type='folder',
            metadata=metadata or {'folder': folder_path, 'recursive': recursive}
        )
        
        self.active_jobs[job_id] = job
        
        try:
            job.status = IngestionStatus.VALIDATING
            
            # Descubrir archivos en la carpeta
            discovered_files = await self.folder_processor.discover_files(
                folder_path,
                self.supported_formats,
                recursive
            )
            
            job.total_files = len(discovered_files)
            logger.info(f"Descubiertos {job.total_files} archivos válidos en {folder_path}")
            
            if job.total_files == 0:
                job.status = IngestionStatus.COMPLETED
                job.end_time = datetime.now()
                return job
            
            # Procesar archivos descubiertos
            job.status = IngestionStatus.PROCESSING
            
            # Procesar en lotes para optimizar memoria
            batch_size = 10
            for i in range(0, len(discovered_files), batch_size):
                batch = discovered_files[i:i+batch_size]
                
                batch_results = await asyncio.gather(*[
                    self._process_file_from_path(file_path, user_id)
                    for file_path in batch
                ], return_exceptions=True)
                
                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        job.errors.append({
                            'file': batch[idx],
                            'error': str(result)
                        })
                        job.failed_files += 1
                    else:
                        job.files.append(result)
                        job.processed_files += 1
            
            # Determinar estado final
            if job.processed_files == job.total_files:
                job.status = IngestionStatus.COMPLETED
            elif job.processed_files > 0:
                job.status = IngestionStatus.PARTIALLY_COMPLETED
            else:
                job.status = IngestionStatus.FAILED
                
        except Exception as e:
            logger.error(f"Error en ingesta de carpeta: {e}")
            job.status = IngestionStatus.FAILED
            job.errors.append({'general': str(e)})
        
        finally:
            job.end_time = datetime.now()
            
        return job
    
    async def ingest_markdown_sources(
        self,
        markdown_content: str,
        user_id: str,
        source_name: str = "markdown_sources",
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionJob:
        """
        Procesa un documento markdown con fuentes estructuradas
        
        Args:
            markdown_content: Contenido del markdown
            user_id: ID del usuario
            source_name: Nombre del documento fuente
            metadata: Metadata adicional
            
        Returns:
            IngestionJob con el estado del proceso
        """
        job_id = self._generate_job_id(user_id)
        job = IngestionJob(
            job_id=job_id,
            type='markdown_sources',
            metadata=metadata or {'source_name': source_name}
        )
        
        self.active_jobs[job_id] = job
        
        try:
            job.status = IngestionStatus.VALIDATING
            
            # Parsear fuentes del markdown
            sources = await self.markdown_parser.parse_sources(markdown_content)
            
            if not sources:
                job.status = IngestionStatus.FAILED
                job.errors.append({
                    'general': 'No se encontraron fuentes válidas en el markdown'
                })
                job.end_time = datetime.now()
                return job
            
            job.total_files = len(sources)
            logger.info(f"Parseadas {job.total_files} fuentes del markdown")
            
            # Procesar cada fuente como un documento
            job.status = IngestionStatus.PROCESSING
            
            for source in sources:
                try:
                    # Convertir fuente a documento procesable
                    document = await self._create_document_from_source(
                        source,
                        source_name,
                        user_id
                    )
                    
                    # Indexar documento
                    result = await self._index_document(document, user_id)
                    
                    job.files.append(result)
                    job.processed_files += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando fuente {source.get('id', 'unknown')}: {e}")
                    job.errors.append({
                        'source': source.get('id', 'unknown'),
                        'error': str(e)
                    })
                    job.failed_files += 1
            
            # Estado final
            if job.processed_files == job.total_files:
                job.status = IngestionStatus.COMPLETED
            elif job.processed_files > 0:
                job.status = IngestionStatus.PARTIALLY_COMPLETED
            else:
                job.status = IngestionStatus.FAILED
                
        except Exception as e:
            logger.error(f"Error en ingesta de fuentes markdown: {e}")
            job.status = IngestionStatus.FAILED
            job.errors.append({'general': str(e)})
        
        finally:
            job.end_time = datetime.now()
            
        return job
    
    async def _process_single_file(
        self,
        file: Any,
        user_id: str,
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Procesa un único archivo"""
        
        # Determinar el tipo de procesamiento según el formato
        file_extension = validation_result['extension']
        file_category = validation_result['category']
        
        # Seleccionar agente apropiado
        agent = await self.agent_orchestrator.select_agent(
            file_type=file_extension,
            category=file_category
        )
        
        # Procesar con el agente seleccionado
        processed_content = await agent.process(file)
        
        # Generar embeddings y almacenar
        result = await self.orchestrator.process_document(
            content=processed_content,
            metadata={
                'user_id': user_id,
                'file_name': file.name,
                'file_type': file_extension,
                'category': file_category,
                'size': validation_result['size'],
                'upload_time': datetime.now().isoformat()
            }
        )
        
        return {
            'file_name': file.name,
            'status': 'success',
            'document_id': result.get('document_id'),
            'chunks': result.get('chunks', 0),
            'processing_time': result.get('processing_time')
        }
    
    async def _process_file_from_path(
        self,
        file_path: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Procesa un archivo desde una ruta del sistema"""
        
        # Abrir y procesar el archivo
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Crear objeto similar a un archivo subido
        class FileWrapper:
            def __init__(self, content, name):
                self.content = content
                self.name = name
                
            def read(self):
                return self.content
        
        wrapped_file = FileWrapper(file_content, file_name)
        
        # Validar archivo
        validation_result = await self.validator.validate_file(
            wrapped_file,
            self.max_file_size,
            self.supported_formats
        )
        
        if not validation_result['valid']:
            raise ValueError(f"Archivo inválido: {validation_result['error']}")
        
        # Procesar archivo
        return await self._process_single_file(
            wrapped_file,
            user_id,
            validation_result
        )
    
    async def _create_document_from_source(
        self,
        source: Dict[str, Any],
        source_document: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Crea un documento procesable desde una fuente parseada"""
        
        # Formatear contenido como documento
        content = f"""
# Fuente: {source.get('id', 'Unknown')}

**Tipo:** {source.get('type', 'N/A')}
**Título:** {source.get('title', 'N/A')}
**Autor(es):** {source.get('authors', 'N/A')}
**Editorial/Origen:** {source.get('publisher', 'N/A')}
**Año:** {source.get('year', 'N/A')}
**URL/DOI:** {source.get('url', 'N/A')}
**Citación:** {source.get('citation', 'N/A')}
**Documento Fuente:** {source_document}

## Contenido adicional
{source.get('additional_content', '')}
"""
        
        return {
            'content': content,
            'metadata': {
                'source_id': source.get('id'),
                'type': 'bibliographic_source',
                'source_type': source.get('type'),
                'title': source.get('title'),
                'authors': source.get('authors'),
                'year': source.get('year'),
                'user_id': user_id,
                'source_document': source_document
            }
        }
    
    async def _index_document(
        self,
        document: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Indexa un documento en el sistema RAG"""
        
        result = await self.orchestrator.process_document(
            content=document['content'],
            metadata=document['metadata']
        )
        
        return {
            'document_id': result.get('document_id'),
            'source_id': document['metadata'].get('source_id'),
            'status': 'indexed',
            'chunks': result.get('chunks', 0)
        }
    
    def _generate_job_id(self, user_id: str) -> str:
        """Genera un ID único para el trabajo"""
        timestamp = datetime.now().isoformat()
        data = f"{user_id}-{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        """Obtiene el estado de un trabajo"""
        return self.active_jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> List[IngestionJob]:
        """Obtiene todos los trabajos de un usuario"""
        user_jobs = []
        for job in self.active_jobs.values():
            if job.metadata.get('user_id') == user_id:
                user_jobs.append(job)
        return sorted(user_jobs, key=lambda x: x.start_time, reverse=True)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancela un trabajo en progreso"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [IngestionStatus.PENDING, IngestionStatus.PROCESSING]:
                job.status = IngestionStatus.FAILED
                job.errors.append({'general': 'Cancelado por el usuario'})
                job.end_time = datetime.now()
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de ingesta"""
        total_jobs = len(self.active_jobs)
        completed_jobs = sum(1 for job in self.active_jobs.values() 
                           if job.status == IngestionStatus.COMPLETED)
        failed_jobs = sum(1 for job in self.active_jobs.values() 
                         if job.status == IngestionStatus.FAILED)
        processing_jobs = sum(1 for job in self.active_jobs.values() 
                            if job.status == IngestionStatus.PROCESSING)
        
        total_files = sum(job.total_files for job in self.active_jobs.values())
        processed_files = sum(job.processed_files for job in self.active_jobs.values())
        failed_files = sum(job.failed_files for job in self.active_jobs.values())
        
        return {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'processing_jobs': processing_jobs,
            'total_files': total_files,
            'processed_files': processed_files,
            'failed_files': failed_files,
            'success_rate': (processed_files / total_files * 100) if total_files > 0 else 0
        }
```

## 2. Procesador de Carpetas

### `app/ingestion/folder_processor.py`

```python
"""
Procesador de Carpetas para el Sistema de Ingesta
Descubre y gestiona archivos en carpetas y subcarpetas
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
import mimetypes
from app.common.logger import Logger

logger = Logger(__name__)

class FolderProcessor:
    """
    Procesador especializado para carpetas y estructuras de directorios
    """
    
    def __init__(self):
        """Inicializa el procesador de carpetas"""
        self.ignored_folders = {
            '__pycache__', '.git', '.svn', 'node_modules',
            '.idea', '.vscode', 'venv', 'env', '.env'
        }
        self.ignored_files = {
            '.DS_Store', 'Thumbs.db', 'desktop.ini'
        }
        
    async def discover_files(
        self,
        folder_path: str,
        supported_formats: Dict[str, List[str]],
        recursive: bool = True,
        max_depth: int = 10
    ) -> List[str]:
        """
        Descubre archivos válidos en una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            supported_formats: Formatos soportados por categoría
            recursive: Si buscar en subcarpetas
            max_depth: Profundidad máxima de búsqueda
            
        Returns:
            Lista de rutas de archivos válidos
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise ValueError(f"La carpeta no existe: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"La ruta no es una carpeta: {folder_path}")
        
        # Crear conjunto de extensiones válidas
        valid_extensions = set()
        for extensions in supported_formats.values():
            valid_extensions.update(extensions)
        
        discovered_files = []
        
        # Función de búsqueda recursiva
        async def search_directory(
            directory: Path,
            current_depth: int = 0
        ) -> List[str]:
            """Busca archivos en un directorio"""
            files = []
            
            if current_depth > max_depth:
                logger.warning(f"Profundidad máxima alcanzada en: {directory}")
                return files
            
            try:
                for item in directory.iterdir():
                    # Ignorar elementos ocultos
                    if item.name.startswith('.'):
                        continue
                    
                    if item.is_file():
                        # Verificar si es un archivo ignorado
                        if item.name in self.ignored_files:
                            continue
                        
                        # Verificar extensión
                        extension = item.suffix.lower()
                        if extension in valid_extensions:
                            files.append(str(item.absolute()))
                            logger.debug(f"Archivo descubierto: {item.name}")
                    
                    elif item.is_dir() and recursive:
                        # Verificar si es una carpeta ignorada
                        if item.name in self.ignored_folders:
                            continue
                        
                        # Buscar recursivamente
                        subdir_files = await search_directory(
                            item,
                            current_depth + 1
                        )
                        files.extend(subdir_files)
                        
            except PermissionError:
                logger.warning(f"Sin permisos para acceder a: {directory}")
            except Exception as e:
                logger.error(f"Error explorando directorio {directory}: {e}")
            
            return files
        
        # Iniciar búsqueda
        discovered_files = await search_directory(folder_path)
        
        logger.info(f"Descubiertos {len(discovered_files)} archivos válidos en {folder_path}")
        
        return discovered_files
    
    async def analyze_folder_structure(
        self,
        folder_path: str
    ) -> Dict[str, Any]:
        """
        Analiza la estructura de una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            Análisis de la estructura de la carpeta
        """
        folder_path = Path(folder_path)
        
        structure = {
            'path': str(folder_path),
            'name': folder_path.name,
            'total_size': 0,
            'file_count': 0,
            'folder_count': 0,
            'file_types': {},
            'largest_files': [],
            'tree_structure': {}
        }
        
        # Función para construir el árbol
        def build_tree(directory: Path, max_depth: int = 3, current_depth: int = 0):
            """Construye un árbol de la estructura del directorio"""
            if current_depth >= max_depth:
                return {'...': 'max depth reached'}
            
            tree = {}
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        size = item.stat().st_size
                        tree[item.name] = f"{self._format_size(size)}"
                        
                        # Actualizar estadísticas
                        structure['file_count'] += 1
                        structure['total_size'] += size
                        
                        # Tipo de archivo
                        ext = item.suffix.lower()
                        structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                        
                        # Archivos más grandes
                        structure['largest_files'].append({
                            'name': item.name,
                            'path': str(item),
                            'size': size
                        })
                    
                    elif item.is_dir() and item.name not in self.ignored_folders:
                        structure['folder_count'] += 1
                        tree[item.name + '/'] = build_tree(item, max_depth, current_depth + 1)
                        
            except PermissionError:
                tree['<sin permisos>'] = None
            except Exception as e:
                tree[f'<error: {str(e)}>'] = None
            
            return tree
        
        # Analizar estructura
        structure['tree_structure'] = build_tree(folder_path)
        
        # Ordenar archivos más grandes
        structure['largest_files'].sort(key=lambda x: x['size'], reverse=True)
        structure['largest_files'] = structure['largest_files'][:10]  # Top 10
        
        # Formatear tamaño total
        structure['total_size_formatted'] = self._format_size(structure['total_size'])
        
        return structure
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatea un tamaño en bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    async def create_folder_report(
        self,
        folder_path: str,
        supported_formats: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Crea un informe detallado de una carpeta
        
        Args:
            folder_path: Ruta de la carpeta
            supported_formats: Formatos soportados
            
        Returns:
            Informe detallado de la carpeta
        """
        # Descubrir archivos
        files = await self.discover_files(folder_path, supported_formats)
        
        # Analizar estructura
        structure = await self.analyze_folder_structure(folder_path)
        
        # Categorizar archivos descubiertos
        categorized_files = {
            'documents': [],
            'images': [],
            'code': [],
            'multimedia': [],
            'archives': [],
            'other': []
        }
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            extension = os.path.splitext(file_name)[1].lower()
            
            categorized = False
            for category, extensions in supported_formats.items():
                if extension in extensions:
                    if category in categorized_files:
                        categorized_files[category].append({
                            'name': file_name,
                            'path': file_path,
                            'extension': extension
                        })
                        categorized = True
                        break
            
            if not categorized:
                categorized_files['other'].append({
                    'name': file_name,
                    'path': file_path,
                    'extension': extension
                })
        
        return {
            'folder_info': structure,
            'discovered_files': {
                'total': len(files),
                'by_category': {
                    category: len(files_list)
                    for category, files_list in categorized_files.items()
                },
                'details': categorized_files
            },
            'recommendations': self._generate_recommendations(structure, categorized_files)
        }
    
    def _generate_recommendations(
        self,
        structure: Dict[str, Any],
        categorized_files: Dict[str, List[Dict]]
    ) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Verificar tamaño total
        if structure['total_size'] > 1024 * 1024 * 1024:  # > 1GB
            recommendations.append(
                "La carpeta contiene más de 1GB de datos. "
                "Considera procesar en lotes más pequeños."
            )
        
        # Verificar cantidad de archivos
        total_files = sum(len(files) for files in categorized_files.values())
        if total_files > 100:
            recommendations.append(
                f"Se encontraron {total_files} archivos. "
                "El procesamiento podría tomar tiempo considerable."
            )
        
        # Verificar archivos grandes
        if structure['largest_files']:
            largest = structure['largest_files'][0]
            if largest['size'] > 200 * 1024 * 1024:  # > 200MB
                recommendations.append(
                    f"El archivo más grande ({largest['name']}) excede 200MB "
                    "y no podrá ser procesado."
                )
        
        # Verificar tipos de archivo predominantes
        if categorized_files['images'] and len(categorized_files['images']) > total_files * 0.5:
            recommendations.append(
                "La mayoría de archivos son imágenes. "
                "Considera activar el procesamiento OCR si contienen texto."
            )
        
        if categorized_files['code'] and len(categorized_files['code']) > total_files * 0.3:
            recommendations.append(
                "Se detectaron múltiples archivos de código. "
                "Se utilizará el agente especializado en código."
            )
        
        return recommendations
```

## 3. Parser de Markdown con Fuentes

### `app/ingestion/markdown_source_parser.py`

```python
"""
Parser para documentos Markdown con fuentes estructuradas
Extrae y procesa fuentes bibliográficas en formato específico
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.common.logger import Logger

logger = Logger(__name__)

@dataclass
class BibliographicSource:
    """Representa una fuente bibliográfica estructurada"""
    id: str
    type: str
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None
    citation: Optional[str] = None
    source_document: Optional[str] = None
    additional_content: Optional[str] = None

class MarkdownSourceParser:
    """
    Parser especializado para extraer fuentes bibliográficas
    de documentos markdown con formato estructurado
    """
    
    def __init__(self):
        """Inicializa el parser de fuentes markdown"""
        # Patrones regex para extracción
        self.patterns = {
            'source_block': re.compile(
                r'\*\*ID:\*\*\s*\[([^\]]+)\](.*?)(?=\*\*ID:\*\*|\Z)',
                re.DOTALL | re.MULTILINE
            ),
            'field': re.compile(
                r'\*\*([^:]+):\*\*\s*([^\n]+)',
                re.MULTILINE
            )
        }
        
        # Mapeo de campos
        self.field_mapping = {
            'Type': 'type',
            'Tipo': 'type',
            'Title': 'title',
            'Título': 'title',
            'Author(s)': 'authors',
            'Autor(es)': 'authors',
            'Publisher/Origin': 'publisher',
            'Editorial/Origen': 'publisher',
            'Year': 'year',
            'Año': 'year',
            'URL/DOI/Identifier': 'url',
            'URL/DOI/Identificador': 'url',
            'Citation': 'citation',
            'Citación': 'citation',
            'Cita': 'citation',
            'Source_Document': 'source_document',
            'Documento_Fuente': 'source_document'
        }
        
        logger.info("Parser de fuentes Markdown inicializado")
    
    async def parse_sources(
        self,
        markdown_content: str
    ) -> List[Dict[str, Any]]:
        """
        Extrae fuentes bibliográficas del contenido markdown
        
        Args:
            markdown_content: Contenido del documento markdown
            
        Returns:
            Lista de fuentes parseadas
        """
        sources = []
        
        try:
            # Buscar todos los bloques de fuente
            source_blocks = self.patterns['source_block'].findall(markdown_content)
            
            for source_id, block_content in source_blocks:
                source = await self._parse_single_source(source_id, block_content)
                if source:
                    sources.append(source)
            
            logger.info(f"Parseadas {len(sources)} fuentes del documento")
            
        except Exception as e:
            logger.error(f"Error parseando fuentes markdown: {e}")
        
        return sources
    
    async def _parse_single_source(
        self,
        source_id: str,
        block_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parsea una única fuente bibliográfica
        
        Args:
            source_id: ID de la fuente
            block_content: Contenido del bloque de la fuente
            
        Returns:
            Diccionario con los datos de la fuente
        """
        try:
            source_data = {
                'id': source_id.strip(),
                'type': 'N/A',
                'title': 'N/A',
                'authors': 'N/A',
                'publisher': 'N/A',
                'year': 'N/A',
                'url': 'N/A',
                'citation': 'N/A',
                'source_document': 'N/A',
                'additional_content': ''
            }
            
            # Extraer campos estructurados
            fields = self.patterns['field'].findall(block_content)
            
            for field_name, field_value in fields:
                field_name = field_name.strip()
                field_value = field_value.strip()
                
                # Mapear al nombre de campo interno
                if field_name in self.field_mapping:
                    internal_name = self.field_mapping[field_name]
                    if field_value and field_value.lower() != 'n/a':
                        source_data[internal_name] = field_value
            
            # Extraer contenido adicional (texto después de los campos)
            # Buscar el último campo y tomar todo lo que viene después
            last_field_match = list(self.patterns['field'].finditer(block_content))
            if last_field_match:
                last_position = last_field_match[-1].end()
                additional = block_content[last_position:].strip()
                if additional:
                    source_data['additional_content'] = additional
            
            # Validar que al menos tenga título o ID válido
            if source_data['title'] == 'N/A' and not source_data['id']:
                logger.warning(f"Fuente sin título ni ID válido: {source_id}")
                return None
            
            # Procesar y limpiar campos específicos
            source_data = await self._process_fields(source_data)
            
            return source_data
            
        except Exception as e:
            logger.error(f"Error parseando fuente {source_id}: {e}")
            return None
    
    async def _process_fields(
        self,
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa y limpia los campos de una fuente
        
        Args:
            source_data: Datos de la fuente sin procesar
            
        Returns:
            Datos de la fuente procesados
        """
        # Procesar autores (separar por comas si hay múltiples)
        if source_data['authors'] != 'N/A':
            authors = source_data['authors']
            # Limpiar y formatear autores
            if ',' in authors or ';' in authors:
                # Múltiples autores
                authors = re.split(r'[,;]', authors)
                authors = [a.strip() for a in authors if a.strip()]
                source_data['authors'] = '; '.join(authors)
        
        # Procesar año (extraer solo el año si hay más información)
        if source_data['year'] != 'N/A':
            year_match = re.search(r'\b(19|20)\d{2}\b', source_data['year'])
            if year_match:
                source_data['year'] = year_match.group()
        
        # Procesar URL/DOI
        if source_data['url'] != 'N/A':
            url = source_data['url']
            # Detectar si es un DOI
            if 'doi.org' in url or url.startswith('10.'):
                if not url.startswith('http'):
                    source_data['url'] = f"https://doi.org/{url}"
            # Asegurar que las URLs tengan protocolo
            elif not url.startswith(('http://', 'https://', 'ftp://')):
                # Si parece una URL web, agregar https
                if '.' in url:
                    source_data['url'] = f"https://{url}"
        
        # Clasificar tipo de fuente si es genérico
        if source_data['type'] in ['N/A', 'Document', 'Documento']:
            source_data['type'] = await self._infer_source_type(source_data)
        
        return source_data
    
    async def _infer_source_type(
        self,
        source_data: Dict[str, Any]
    ) -> str:
        """
        Infiere el tipo de fuente basándose en sus campos
        
        Args:
            source_data: Datos de la fuente
            
        Returns:
            Tipo inferido de la fuente
        """
        # Patrones para identificar tipos de fuentes
        url = source_data.get('url', '').lower()
        title = source_data.get('title', '').lower()
        publisher = source_data.get('publisher', '').lower()
        
        # Detectar artículos académicos
        if 'doi.org' in url or 'arxiv' in url:
            return 'Artículo Académico'
        
        # Detectar libros
        if any(word in publisher for word in ['press', 'editorial', 'publishing']):
            return 'Libro'
        
        # Detectar software/código
        if 'github' in url or 'gitlab' in url or 'bitbucket' in url:
            return 'Repositorio de Código'
        
        if any(word in title for word in ['package', 'library', 'framework', 'api']):
            return 'Herramienta de Software'
        
        # Detectar documentación
        if 'docs' in url or 'documentation' in title:
            return 'Documentación'
        
        # Detectar conferencias
        if any(word in publisher for word in ['conference', 'symposium', 'workshop']):
            return 'Conferencia'
        
        # Detectar sitios web
        if url != 'N/A' and not any(x in url for x in ['pdf', 'doi', 'arxiv']):
            return 'Sitio Web'
        
        # Por defecto
        return 'Documento'
    
    async def validate_source_format(
        self,
        markdown_content: str
    ) -> Dict[str, Any]:
        """
        Valida que el formato del markdown cumpla con la estructura esperada
        
        Args:
            markdown_content: Contenido del markdown
            
        Returns:
            Resultado de la validación con detalles
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'source_count': 0
        }
        
        # Buscar bloques de fuente
        source_blocks = self.patterns['source_block'].findall(markdown_content)
        validation_result['source_count'] = len(source_blocks)
        
        if len(source_blocks) == 0:
            validation_result['valid'] = False
            validation_result['errors'].append(
                "No se encontraron fuentes con el formato esperado. "
                "Asegúrate de usar **ID:** [SRC-XXX] para cada fuente."
            )
            return validation_result
        
        # Validar cada fuente
        for idx, (source_id, block_content) in enumerate(source_blocks, 1):
            # Validar formato del ID
            if not re.match(r'^SRC-\w+$', source_id.strip()):
                validation_result['warnings'].append(
                    f"Fuente {idx}: El ID '{source_id}' no sigue el formato "
                    "recomendado SRC-XXX"
                )
            
            # Verificar campos requeridos
            fields = self.patterns['field'].findall(block_content)
            field_names = [field[0].strip() for field in fields]
            
            required_fields = ['Type', 'Title', 'Tipo', 'Título']
            has_type = any(f in field_names for f in ['Type', 'Tipo'])
            has_title = any(f in field_names for f in ['Title', 'Título'])
            
            if not has_type:
                validation_result['errors'].append(
                    f"Fuente {source_id}: Falta el campo **Type:** o **Tipo:**"
                )
                validation_result['valid'] = False
            
            if not has_title:
                validation_result['errors'].append(
                    f"Fuente {source_id}: Falta el campo **Title:** o **Título:**"
                )
                validation_result['valid'] = False
        
        # Advertencias adicionales
        if validation_result['source_count'] > 100:
            validation_result['warnings'].append(
                f"El documento contiene {validation_result['source_count']} fuentes. "
                "El procesamiento podría tomar tiempo considerable."
            )
        
        return validation_result
    
    async def generate_template(
        self,
        language: str = 'es'
    ) -> str:
        """
        Genera una plantilla de ejemplo para el formato de fuentes
        
        Args:
            language: Idioma de la plantilla ('es' o 'en')
            
        Returns:
            Plantilla en markdown
        """
        if language == 'es':
            template = """# Plantilla de Fuentes Bibliográficas

## Instrucciones
Cada fuente debe seguir exactamente este formato:

**ID:** [SRC-001]
**Tipo:** [Tipo de fuente, e.g., Documento Académico, Herramienta de Software]
**Título:** [Título del recurso]
**Autor(es):** [Autor(es) o N/A]
**Editorial/Origen:** [Entidad publicadora, revista, conferencia, empresa, o N/A]
**Año:** [Año de publicación o N/A]
**URL/DOI/Identificador:** [Enlace, DOI, o identificador único, o N/A]
**Citación:** [Cita completa si está disponible, o N/A]
**Documento_Fuente:** [Nombre del documento de origen]

## Ejemplo de Fuentes

**ID:** [SRC-001]
**Tipo:** Artículo Académico
**Título:** Deep Learning for Natural Language Processing
**Autor(es):** Smith, J.; Johnson, K.
**Editorial/Origen:** Journal of AI Research
**Año:** 2023
**URL/DOI/Identificador:** https://doi.org/10.1234/jair.2023.001
**Citación:** Smith, J. & Johnson, K. (2023). Deep Learning for NLP. Journal of AI Research, 45(2), 123-145.
**Documento_Fuente:** Bibliografia_Tesis.md

**ID:** [SRC-002]
**Tipo:** Herramienta de Software
**Título:** LangChain Python Library
**Autor(es):** Harrison Chase
**Editorial/Origen:** LangChain Inc.
**Año:** 2024
**URL/DOI/Identificador:** https://github.com/langchain-ai/langchain
**Citación:** N/A
**Documento_Fuente:** Herramientas_Proyecto.md

**ID:** [SRC-003]
**Tipo:** Libro
**Título:** Inteligencia Artificial: Un Enfoque Moderno
**Autor(es):** Russell, S.; Norvig, P.
**Editorial/Origen:** Pearson Education
**Año:** 2022
**URL/DOI/Identificador:** N/A
**Citación:** Russell, S. & Norvig, P. (2022). Inteligencia Artificial: Un Enfoque Moderno (4ta ed.). Pearson.
**Documento_Fuente:** Referencias_IA.md
"""
        else:  # English
            template = """# Bibliographic Sources Template

## Instructions
Each source must follow exactly this format:

**ID:** [SRC-001]
**Type:** [Source type, e.g., Academic Paper, Software Tool]
**Title:** [Resource title]
**Author(s):** [Author(s) or N/A]
**Publisher/Origin:** [Publishing entity, journal, conference, company, or N/A]
**Year:** [Publication year or N/A]
**URL/DOI/Identifier:** [Link, DOI, or unique identifier, or N/A]
**Citation:** [Full citation if available, or N/A]
**Source_Document:** [Name of source document]

## Example Sources

**ID:** [SRC-001]
**Type:** Academic Paper
**Title:** Deep Learning for Natural Language Processing
**Author(s):** Smith, J.; Johnson, K.
**Publisher/Origin:** Journal of AI Research
**Year:** 2023
**URL/DOI/Identifier:** https://doi.org/10.1234/jair.2023.001
**Citation:** Smith, J. & Johnson, K. (2023). Deep Learning for NLP. Journal of AI Research, 45(2), 123-145.
**Source_Document:** Thesis_Bibliography.md

**ID:** [SRC-002]
**Type:** Software Tool
**Title:** LangChain Python Library
**Author(s):** Harrison Chase
**Publisher/Origin:** LangChain Inc.
**Year:** 2024
**URL/DOI/Identifier:** https://github.com/langchain-ai/langchain
**Citation:** N/A
**Source_Document:** Project_Tools.md

**ID:** [SRC-003]
**Type:** Book
**Title:** Artificial Intelligence: A Modern Approach
**Author(s):** Russell, S.; Norvig, P.
**Publisher/Origin:** Pearson Education
**Year:** 2022
**URL/DOI/Identifier:** N/A
**Citation:** Russell, S. & Norvig, P. (2022). Artificial Intelligence: A Modern Approach (4th ed.). Pearson.
**Source_Document:** AI_References.md
"""
        
        return template
```

## 4. Interfaz de Usuario Streamlit

### `app/pages/02_📤_Ingesta_Avanzada.py`

```python
"""
Interfaz de Usuario para el Sistema de Ingesta Avanzado
Página de Streamlit para gestión de documentos
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
import tempfile
import os
import json
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

from app.ingestion.advanced_ingestion_system import AdvancedIngestionSystem, IngestionStatus
from app.components.ingestion_ui_components import (
    FileUploader,
    FolderSelector,
    MarkdownEditor,
    JobMonitor,
    StatisticsDisplay
)

# Configuración de la página
st.set_page_config(
    page_title="Ingesta Avanzada - Anclora RAG",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .upload-area {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f0f8ff;
        margin-bottom: 20px;
    }
    
    .stats-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .warning-message {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .job-status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .status-pending { background-color: #6c757d; color: white; }
    .status-processing { background-color: #007bff; color: white; }
    .status-completed { background-color: #28a745; color: white; }
    .status-failed { background-color: #dc3545; color: white; }
    .status-partially { background-color: #ffc107; color: black; }
</style>
""", unsafe_allow_html=True)

# Inicializar sistema de ingesta
@st.cache_resource
def get_ingestion_system():
    return AdvancedIngestionSystem()

ingestion_system = get_ingestion_system()

# Título y descripción
st.title("📤 Sistema de Ingesta Avanzado")
st.markdown("""
Sistema completo para la ingesta de documentos con soporte para:
- **Archivos individuales**: Hasta 200MB por archivo
- **Carpetas completas**: Procesamiento automático de archivos válidos
- **Fuentes bibliográficas**: Formato Markdown estructurado
""")

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📎 Archivos Individuales",
    "📁 Carpetas",
    "📝 Fuentes Markdown",
    "📊 Monitor de Trabajos",
    "📈 Estadísticas"
])

# Tab 1: Archivos Individuales
with tab1:
    st.header("Carga de Archivos Individuales")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Área de carga de archivos
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Arrastra archivos aquí o haz clic para seleccionar",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'doc', 'txt', 'md', 'pptx', 'xlsx', 'csv',
                  'jpg', 'jpeg', 'png', 'py', 'js', 'java', 'zip', 'rar'],
            key="file_uploader",
            help="Tamaño máximo: 200MB por archivo"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} archivo(s) seleccionado(s)")
            
            # Mostrar información de archivos
            file_info = []
            total_size = 0
            
            for file in uploaded_files:
                size = len(file.read())
                file.seek(0)  # Reset file pointer
                total_size += size
                
                file_info.append({
                    'Nombre': file.name,
                    'Tipo': file.type or 'Unknown',
                    'Tamaño': f"{size / 1024 / 1024:.2f} MB"
                })
            
            df_files = pd.DataFrame(file_info)
            st.dataframe(df_files, use_container_width=True)
            
            st.info(f"**Tamaño total:** {total_size / 1024 / 1024:.2f} MB")
            
            # Botón de procesamiento
            if st.button("🚀 Procesar Archivos", type="primary", use_container_width=True):
                with st.spinner("Procesando archivos..."):
                    # Ejecutar ingesta asíncrona
                    async def run_ingestion():
                        job = await ingestion_system.ingest_files(
                            files=uploaded_files,
                            user_id=st.session_state.get('user_id', 'default'),
                            metadata={'source': 'streamlit_ui'}
                        )
                        return job
                    
                    job = asyncio.run(run_ingestion())
                    
                    # Mostrar resultados
                    if job.status == IngestionStatus.COMPLETED:
                        st.balloons()
                        st.success(f"""
                        ✅ **Procesamiento completado exitosamente**
                        - Archivos procesados: {job.processed_files}/{job.total_files}
                        - Tiempo total: {(job.end_time - job.start_time).total_seconds():.2f}s
                        """)
                    elif job.status == IngestionStatus.PARTIALLY_COMPLETED:
                        st.warning(f"""
                        ⚠️ **Procesamiento parcialmente completado**
                        - Archivos procesados: {job.processed_files}/{job.total_files}
                        - Archivos con errores: {job.failed_files}
                        """)
                        
                        if job.errors:
                            with st.expander("Ver errores"):
                                for error in job.errors:
                                    st.error(f"**{error.get('file', 'Unknown')}:** {error.get('error', 'Unknown error')}")
                    else:
                        st.error(f"""
                        ❌ **Error en el procesamiento**
                        - Estado: {job.status.value}
                        - Errores: {len(job.errors)}
                        """)
    
    with col2:
        # Panel de información
        st.markdown("### 📋 Formatos Soportados")
        
        with st.expander("Ver todos los formatos", expanded=False):
            for category, extensions in ingestion_system.supported_formats.items():
                st.markdown(f"**{category.title()}:**")
                st.markdown(", ".join(extensions))
        
        st.markdown("### 💡 Consejos")
        st.info("""
        - Puedes seleccionar múltiples archivos a la vez
        - El límite es 200MB por archivo
        - Los archivos comprimidos se descomprimirán automáticamente
        - El sistema detectará automáticamente el tipo de contenido
        """)

# Tab 2: Carpetas
with tab2:
    st.header("Procesamiento de Carpetas")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Selector de carpeta
        folder_path = st.text_input(
            "Ruta de la carpeta",
            placeholder="/ruta/a/tu/carpeta",
            help="Introduce la ruta completa de la carpeta a procesar"
        )
        
        recursive = st.checkbox(
            "Procesar subcarpetas recursivamente",
            value=True,
            help="Buscar archivos en todas las subcarpetas"
        )
        
        if folder_path:
            # Botón de análisis
            if st.button("🔍 Analizar Carpeta", use_container_width=True):
                with st.spinner("Analizando estructura de carpeta..."):
                    try:
                        async def analyze_folder():
                            report = await ingestion_system.folder_processor.create_folder_report(
                                folder_path,
                                ingestion_system.supported_formats
                            )
                            return report
                        
                        report = asyncio.run(analyze_folder())
                        
                        # Guardar reporte en sesión
                        st.session_state['folder_report'] = report
                        
                        # Mostrar resumen
                        st.success(f"✅ Análisis completado: {report['discovered_files']['total']} archivos encontrados")
                        
                    except Exception as e:
                        st.error(f"Error analizando carpeta: {str(e)}")
            
            # Mostrar reporte si existe
            if 'folder_report' in st.session_state:
                report = st.session_state['folder_report']
                
                # Estadísticas generales
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Total de Archivos", report['discovered_files']['total'])
                
                with col_stat2:
                    st.metric("Tamaño Total", 
                             report['folder_info'].get('total_size_formatted', 'N/A'))
                
                with col_stat3:
                    st.metric("Subcarpetas", report['folder_info']['folder_count'])
                
                
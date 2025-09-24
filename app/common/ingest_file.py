"""Utilities to ingest files into the vector database."""
from __future__ import annotations

import logging
import os
import tempfile
import uuid
from contextlib import contextmanager
from typing import Any, List, Tuple, Optional
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import streamlit as st
# Provide a lightweight fallback when ``langchain`` is not available during tests.
try:  # pragma: no cover - prefer the real implementation when installed
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
except Exception:  # pragma: no cover - fallback path used in constrained environments
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        """Minimal splitter that returns documents unchanged."""

        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 0, separators: Optional[List[str]] = None) -> None:  # noqa: D401
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators or ["\n\n", "\n", " "]

        def split_documents(self, documents):
            return list(documents)
import sys
import os

# Add the app directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from agents import (
    BaseFileIngestor,
    CodeIngestor,
    DocumentIngestor,
    MultimediaIngestor,
    ArchiveIngestor,
    refresh_document_loaders,
)

# Import security scanner and analytics
try:
    from security import scan_file_for_conversion, is_file_safe_for_conversion, ScanResult
    from analytics import record_security_event
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    # El mensaje se mostrará durante el procesamiento de archivos
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from common.chroma_db_settings import Chroma
from common.embeddings_manager import get_embeddings_manager

# Custom security exception
class SecurityError(Exception):
    """Excepción lanzada cuando se detecta una amenaza de seguridad."""
    pass


try:
    from common.chroma_db_settings import get_unique_sources_df as _get_unique_sources_df
except (ImportError, AttributeError):  # pragma: no cover - fallback for lightweight stubs
    def _get_unique_sources_df(chroma_settings) -> pd.DataFrame:  # type: ignore
        logger.warning("Using fallback get_unique_sources_df function - ChromaDB settings not available")
        return pd.DataFrame(columns=["uploaded_file_name", "domain", "collection"])
from common.constants import CHROMA_SETTINGS
from common.text_normalization import Document, normalize_documents_nfc
from common.privacy import PrivacyManager

get_unique_sources_df = _get_unique_sources_df

logger = logging.getLogger(__name__)

# Cola de procesamiento global con prioridad por tamaño
processing_queue = queue.PriorityQueue()
processing_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ingest")
processing_status = {}  # {file_id: {"status": "processing", "progress": 0.5, "result": None}}


# Configuración de chunking por dominio
CHUNKING_CONFIG = {
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
            "\n\nSELECT ",  # SQL
            "\n\nCREATE ",
            "\n\nALTER ",
            "\n\n",
            "\n",
            " "
        ]
    },
    "documents": {
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
    "multimedia": {
        "chunk_size": 600,
        "chunk_overlap": 60,
        "separators": [
            "\n\n",
            "\n",
            " "
        ]
    },
    "default": {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "separators": ["\n\n", "\n", " "]
    }
}

# Configuración legacy para compatibilidad
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass(slots=True)
class ProcessedFile:
    """Container holding the normalised documents and their ingestor."""

    documents: List[Document]
    ingestor: BaseFileIngestor

    def __iter__(self):  # type: ignore[override]
        return iter(self.documents)

    def __len__(self) -> int:  # type: ignore[override]
        return len(self.documents)

    def __getitem__(self, item):  # type: ignore[override]
        return self.documents[item]

def get_embeddings(domain: Optional[str] = None) -> Any:
    """Obtain embeddings for the requested domain using the shared manager."""

    return get_embeddings_manager().get_embeddings(domain)

# Ensure the ingestors see the latest loader implementations when the module is re-imported
refresh_document_loaders(force=True)

INGESTORS: Tuple[BaseFileIngestor, ...] = (
    DocumentIngestor,
    CodeIngestor,
    MultimediaIngestor,
    ArchiveIngestor,
)

SUPPORTED_EXTENSIONS = sorted({ext for ingestor in INGESTORS for ext in ingestor.extensions})


def _get_ingestor_for_extension(extension: str) -> BaseFileIngestor:
    for ingestor in INGESTORS:
        if ingestor.supports_extension(extension):
            return ingestor
    raise ValueError(f"Tipo de archivo no soportado: {extension}")


def _get_text_splitter_for_domain(domain: str) -> RecursiveCharacterTextSplitter:
    """Obtiene un text splitter configurado específicamente para el dominio dado."""

    config = CHUNKING_CONFIG.get(domain, CHUNKING_CONFIG["default"])

    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=config.get("separators", ["\n\n", "\n", " "])
    )


@contextmanager
def _temp_file(uploaded_file) -> Iterator[str]:
    tmp_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
    tmp_path = os.path.join(tempfile.gettempdir(), tmp_filename)
    with open(tmp_path, "wb") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
    try:
        yield tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _load_documents(uploaded_file, file_name: str) -> Tuple[List[Document], BaseFileIngestor]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    ingestor = _get_ingestor_for_extension(ext)

    if ingestor is None:
        raise ValueError(f"No ingestor found for extension: {ext}")

    try:
        with _temp_file(uploaded_file) as tmp_path:
            documents = ingestor.load(tmp_path, ext)

        if documents is None:
            raise ValueError(f"Document loader returned None for file: {file_name}")

        if not isinstance(documents, list):
            raise ValueError(f"Document loader returned invalid type {type(documents)} for file: {file_name}")

        for document in documents:
            if document is None:
                continue
            metadata = dict(document.metadata or {})
            metadata.update(
                {
                    "domain": ingestor.domain,
                    "collection": ingestor.collection_name,
                    "uploaded_file_name": file_name,
                }
            )
            document.metadata = metadata

        return documents, ingestor
    except Exception as e:
        logger.error(f"Error loading documents for file {file_name}: {e}")
        raise


class ProcessResult(Sequence[Document]):
    """Wrapper that exposes processed documents while keeping ingestor context."""

    __slots__ = ("_documents", "ingestor", "duplicate")

    def __init__(self, documents: List[Document], ingestor: BaseFileIngestor, duplicate: bool = False) -> None:
        self._documents = documents
        self.ingestor = ingestor
        self.duplicate = duplicate

    def __len__(self) -> int:  # pragma: no cover - trivial delegation
        return len(self._documents)

    def __getitem__(self, index):  # pragma: no cover - trivial delegation
        return self._documents[index]

    def __iter__(self):  # pragma: no cover - trivial delegation
        return iter(self._documents)

    @property
    def documents(self) -> List[Document]:
        return self._documents


def _collection_contains_file(collection, file_name: str) -> bool:
    try:
        results = collection.get(where={"uploaded_file_name": file_name})
    except Exception as e:  # pragma: no cover - chroma specific failure fallback
        logger.warning(f"Error querying collection for file {file_name}: {e}")
        try:
            results = collection.get()
        except Exception as e2:
            logger.error(f"Failed to get collection data for file {file_name}: {e2}")
            return False

    # Handle case where collection.get() returns None
    if results is None:
        logger.warning(f"Collection.get() returned None for file: {file_name}")
        return False

    # Ensure results is a dictionary before accessing keys
    if not isinstance(results, dict):
        logger.warning(f"Collection.get() returned non-dict type {type(results)} for file: {file_name}")
        return False

    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])

    # Check if file exists by ID
    if ids and file_name in ids:
        return True

    # Check if file exists by metadata
    if metadatas:
        return any(
            isinstance(metadata, dict) and metadata.get("uploaded_file_name") == file_name
            for metadata in metadatas
            if metadata is not None
        )

    return False


def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
    """Validate the uploaded file size and extension."""

    if uploaded_file.size > MAX_FILE_SIZE:
        return False, "Archivo demasiado grande (máximo 10MB)"

    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        return False, f"Tipo de archivo no soportado: {file_ext}"

    return True, "Válido"


def load_single_document(uploaded_file, file_name: str) -> Tuple[List[Document], BaseFileIngestor]:
    """Load a document from the uploaded file and return its ingestor."""

    is_valid, message = validate_uploaded_file(uploaded_file)
    if not is_valid:
        raise ValueError(message)

    try:
        logger.info("Cargando documento: %s", uploaded_file.name)
        documents, ingestor = _load_documents(uploaded_file, file_name)

        # Validate that we got valid results
        if documents is None:
            raise ValueError(f"Document loader returned None for file: {file_name}")
        if ingestor is None:
            raise ValueError(f"No ingestor found for file: {file_name}")
        if not isinstance(documents, list):
            raise ValueError(f"Document loader returned invalid type {type(documents)} for file: {file_name}")

        return documents, ingestor
    except Exception as exc:
        logger.error("Error al cargar documento %s: %s", uploaded_file.name, exc)
        raise


def process_file(uploaded_file, file_name: str) -> ProcessResult:
    """Process a file with security scanning before ingestion."""

    # 🔒 SECURITY SCAN: Escanear archivo por malware antes de procesarlo
    if SECURITY_AVAILABLE:
        # Guardar archivo temporalmente para escaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        try:
            # Escanear archivo por amenazas
            scan_result = scan_file_for_conversion(temp_file_path)

            if not scan_result.is_safe:
                # Archivo peligroso detectado
                threat_msg = f"🚨 ARCHIVO BLOQUEADO: {file_name}"
                security_msg = f"Nivel de amenaza: {scan_result.threat_level.upper()}"
                threats_msg = "Amenazas detectadas: " + ", ".join(scan_result.threats_detected)

                st.error(threat_msg)
                st.error(security_msg)
                st.error(threats_msg)

                if scan_result.quarantine_path:
                    st.warning(f"Archivo puesto en cuarentena: {scan_result.quarantine_path}")

                logger.error(f"Archivo bloqueado por seguridad: {file_name} - {scan_result.threat_level}")
                logger.error(f"Amenazas: {scan_result.threats_detected}")

                # Retornar resultado vacío para bloquear procesamiento
                raise SecurityError(f"Archivo bloqueado por seguridad: {scan_result.threat_level}")

            else:
                # Archivo seguro
                st.success(f"✅ Archivo seguro: {file_name}")
                logger.info(f"Archivo aprobado por seguridad: {file_name}")

                # Resetear el puntero del archivo para procesamiento normal
                uploaded_file.seek(0)

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    else:
        # Escaneo deshabilitado - mostrar advertencia
        st.warning("⚠️ Escaneo de seguridad deshabilitado - Procesando sin verificación antimalware")
        logger.warning(f"Procesando archivo sin escaneo de seguridad: {file_name}")

    # Continuar con procesamiento normal si el archivo es seguro
    try:
        documents, ingestor = load_single_document(uploaded_file, file_name)
    except Exception as e:
        logger.error(f"Error loading document {file_name}: {e}")
        raise

    try:
        collection = CHROMA_SETTINGS.get_or_create_collection(ingestor.collection_name)
        if _collection_contains_file(collection, file_name):
            return ProcessResult([], ingestor, duplicate=True)
    except Exception as e:
        logger.error(f"Error checking collection for file {file_name}: {e}")
        raise

    # Usar chunking específico por dominio
    try:
        text_splitter = _get_text_splitter_for_domain(ingestor.domain)
        texts = text_splitter.split_documents(documents)

        # Agregar metadatos de chunking para análisis
        for i, text in enumerate(texts):
            if hasattr(text, 'metadata') and text.metadata:
                text.metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(texts),
                    "chunking_domain": ingestor.domain,
                    "chunk_size_config": CHUNKING_CONFIG.get(ingestor.domain, CHUNKING_CONFIG["default"])["chunk_size"],
                    "chunk_overlap_config": CHUNKING_CONFIG.get(ingestor.domain, CHUNKING_CONFIG["default"])["chunk_overlap"]
                })

        normalized = normalize_documents_nfc(texts)
        return ProcessResult(normalized, ingestor)
    except Exception as e:
        logger.error(f"Error processing documents for file {file_name}: {e}")
        raise

def does_vectorstore_exist(settings, collection_name: str) -> bool:
    """Check if a vectorstore already contains data for *collection_name*."""

    collection = settings.get_or_create_collection(collection_name)
    try:
        return collection.count() > 0
    except Exception:  # pragma: no cover - compatibility fallback
        response = collection.get(include=["ids"])
        return bool(response.get("ids"))

def ingest_file_priority(uploaded_file, file_name, file_size=None):
    """Ingesta archivo con prioridad por tamaño (pequeños primero)."""

    # Calcular tamaño si no se proporciona
    if file_size is None:
        if hasattr(uploaded_file, 'size'):
            file_size = uploaded_file.size
        else:
            # Estimar tamaño leyendo el archivo
            current_pos = uploaded_file.tell() if hasattr(uploaded_file, 'tell') else 0
            uploaded_file.seek(0, 2)  # Ir al final
            file_size = uploaded_file.tell()
            uploaded_file.seek(current_pos)  # Volver a posición original

    # Crear ID único para el archivo
    file_id = f"{file_name}_{int(time.time())}"

    # Prioridad: archivos más pequeños tienen prioridad más alta (número menor)
    # Archivos < 1MB = prioridad 1, < 10MB = prioridad 2, >= 10MB = prioridad 3
    if file_size < 1024 * 1024:  # < 1MB
        priority = 1
    elif file_size < 10 * 1024 * 1024:  # < 10MB
        priority = 2
    else:  # >= 10MB
        priority = 3

    # Inicializar status
    processing_status[file_id] = {
        "status": "queued",
        "progress": 0.0,
        "result": None,
        "file_name": file_name,
        "file_size": file_size,
        "priority": priority,
        "queued_at": time.time()
    }

    # Agregar a cola con prioridad
    processing_queue.put((priority, time.time(), file_id, uploaded_file, file_name))

    # Iniciar procesamiento si no está corriendo
    _start_processing_worker()

    logger.info(f"📋 Archivo {file_name} ({file_size/1024/1024:.1f}MB) agregado a cola con prioridad {priority}")

    return file_id

def ingest_file(uploaded_file, file_name):
    """Process and ingest a file into the vector database (método original)."""

    try:
        logger.info("Iniciando ingesta del archivo: %s", file_name)

        if uploaded_file is None:
            return {"success": False, "error": "Archivo no proporcionado"}

        if not hasattr(uploaded_file, 'name'):
            return {"success": False, "error": "Objeto de archivo inválido"}

        result = process_file(uploaded_file, file_name)

        # Validate result
        if result is None:
            logger.error("process_file returned None for file: %s", file_name)
            return {"success": False, "error": "Error interno: process_file devolvió None"}

        # Convert ProcessResult to dictionary format expected by callers
        if isinstance(result, ProcessResult):
            if result.duplicate:
                logger.warning("Archivo duplicado: %s", file_name)
                return {"success": False, "error": "Archivo ya existe en la base de datos"}
            elif hasattr(result, 'documents') and len(result.documents) > 0:
                logger.info("Archivo ingerido exitosamente: %s", file_name)
                return {"success": True, "message": f"Archivo procesado con {len(result.documents)} documentos"}
            else:
                logger.error("No se generaron documentos para el archivo: %s", file_name)
                return {"success": False, "error": "No se generaron documentos válidos"}
        else:
            # If it's already a dict, return as is
            return result
    except Exception as e:
        logger.error("Error durante la ingesta del archivo %s: %s", file_name, str(e))
        error_msg = str(e)
        if "'NoneType' object has no attribute 'get'" in error_msg:
            error_msg = "Error interno: problema con la conexión a la base de datos vectorial"
        return {"success": False, "error": error_msg}

def _start_processing_worker():
    """Inicia el worker de procesamiento si no está corriendo."""

    # Verificar si ya hay un worker corriendo
    for thread in threading.enumerate():
        if thread.name.startswith("ingest-worker"):
            return  # Ya hay un worker corriendo

    # Iniciar nuevo worker
    worker_thread = threading.Thread(target=_processing_worker, name="ingest-worker", daemon=True)
    worker_thread.start()

def _processing_worker():
    """Worker que procesa archivos de la cola por prioridad."""

    logger.info("🔄 Worker de procesamiento iniciado")

    while True:
        try:
            # Obtener siguiente archivo de la cola (bloquea hasta que haya uno)
            priority, queued_time, file_id, uploaded_file, file_name = processing_queue.get(timeout=30)

            # Actualizar status
            processing_status[file_id]["status"] = "processing"
            processing_status[file_id]["progress"] = 0.1

            logger.info(f"⚡ Procesando {file_name} (prioridad {priority})")

            try:
                # Procesar archivo
                result = process_file(uploaded_file, file_name)

                # Actualizar status exitoso
                processing_status[file_id]["status"] = "completed"
                processing_status[file_id]["progress"] = 1.0
                processing_status[file_id]["result"] = result

                logger.info(f"✅ Completado: {file_name}")

            except Exception as e:
                # Actualizar status fallido
                processing_status[file_id]["status"] = "failed"
                processing_status[file_id]["progress"] = 0.0
                processing_status[file_id]["result"] = {"success": False, "error": str(e)}

                logger.error(f"❌ Error procesando {file_name}: {str(e)}")

            # Marcar tarea como completada
            processing_queue.task_done()

        except queue.Empty:
            # No hay más archivos en cola, terminar worker
            logger.info("🔄 Worker terminado - no hay más archivos en cola")
            break
        except Exception as e:
            logger.error(f"❌ Error en worker: {str(e)}")

def get_processing_status(file_id):
    """Obtiene el status de procesamiento de un archivo."""
    return processing_status.get(file_id, {"status": "not_found", "progress": 0.0})

def get_queue_status():
    """Obtiene status general de la cola de procesamiento."""

    queued = sum(1 for status in processing_status.values() if status["status"] == "queued")
    processing = sum(1 for status in processing_status.values() if status["status"] == "processing")
    completed = sum(1 for status in processing_status.values() if status["status"] == "completed")
    failed = sum(1 for status in processing_status.values() if status["status"] == "failed")

    return {
        "queue_size": processing_queue.qsize(),
        "queued": queued,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total": len(processing_status)
    }

def _original_ingest_file(uploaded_file, file_name):
    """Función original de ingesta (renombrada)."""

    try:
        logger.info("Iniciando ingesta del archivo: %s", file_name)
        result = process_file(uploaded_file, file_name)

        if result.duplicate:
            st.warning("Este archivo ya fue agregado anteriormente.")
            logger.warning("Archivo duplicado: %s", file_name)
            return

        texts = result.documents
        ingestor = result.ingestor
        embeddings = get_embeddings(ingestor.domain)

        # Convert local Document objects to LangChain Document objects
        from langchain_core.documents import Document as LangChainDocument
        langchain_docs = [
            LangChainDocument(page_content=doc.page_content, metadata=doc.metadata)
            for doc in texts
        ]

        spinner_message = f"Creando embeddings para {file_name}..."
        if does_vectorstore_exist(CHROMA_SETTINGS, ingestor.collection_name):
            db = Chroma(
                collection_name=ingestor.collection_name,
                embedding_function=embeddings,
                client=CHROMA_SETTINGS,
            )
            with st.spinner(spinner_message):
                db.add_documents(langchain_docs)
        else:
            st.info("Creando nueva base de datos vectorial...")
            with st.spinner("Creando embeddings. Esto puede tomar algunos minutos..."):
                try:
                    Chroma.from_documents(
                        langchain_docs,
                        embeddings,
                        client=CHROMA_SETTINGS,
                        collection_name=ingestor.collection_name,
                    )
                except TypeError:
                    # Compatibilidad con dobles de prueba minimalistas.
                    Chroma.from_documents(langchain_docs, embeddings, CHROMA_SETTINGS)

        st.success(f"Se agregó el archivo '{file_name}' con éxito.")
        logger.info("Archivo procesado exitosamente: %s", file_name)

    except SecurityError as sec_exc:
        # Manejo específico de errores de seguridad
        security_msg = f"🚨 ARCHIVO BLOQUEADO POR SEGURIDAD: '{file_name}'"
        st.error(security_msg)
        st.error(f"Motivo: {sec_exc}")
        st.warning("El archivo no fue procesado por razones de seguridad.")
        logger.error("Archivo bloqueado por seguridad: %s - %s", file_name, sec_exc)
        return  # No continuar procesamiento

    except Exception as exc:
        error_msg = f"Error al procesar el archivo '{file_name}': {exc}"
        st.error(error_msg)
        logger.error(error_msg)


def delete_file_from_vectordb(filename: str) -> bool:
    """Remove ``filename`` from the knowledge base and temporary storage."""

    manager = PrivacyManager()
    summary = manager.forget_document(filename, requested_by="ingest_module")

    if summary.status != "deleted":
        logger.warning("No se encontraron coincidencias para eliminar el archivo %s", filename)
        return False

    logger.info(
        "Se eliminó el archivo %s de las colecciones %s",
        filename,
        ", ".join(summary.removed_collections) or "-",
    )
    return True


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "delete_file_from_vectordb",
    "does_vectorstore_exist",
    "get_embeddings",
    "get_unique_sources_df",
    "ingest_file",
    "ProcessedFile",
    "load_single_document",
    "process_file",
    "validate_uploaded_file",
]

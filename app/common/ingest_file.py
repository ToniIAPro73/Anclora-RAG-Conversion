"""Utilities to ingest files into the vector database."""
from __future__ import annotations

import logging
import os
import tempfile
import unicodedata
import uuid
import threading
import queue
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import streamlit as st
# Provide a lightweight fallback when ``langchain`` is not available during tests.
try:  # pragma: no cover - prefer the real implementation when installed
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
    from langchain_core.documents import Document as LangChainDocument  # type: ignore
    LANGCHAIN_AVAILABLE = True
except Exception:  # pragma: no cover - fallback path used in constrained environments
    LANGCHAIN_AVAILABLE = False
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        """Minimal splitter that returns documents unchanged."""

        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 0, separators: Optional[List[str]] = None) -> None:  # noqa: D401
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.separators = separators or ["\n\n", "\n", " "]

        def split_documents(self, documents):
            return list(documents)

    # Fallback Document class when langchain is not available
    class LangChainDocument:  # type: ignore
        """Fallback Document class that mimics LangChain Document behavior."""

        def __init__(self, page_content: str, metadata: Optional[dict] = None):
            self.page_content = page_content
            self.metadata = metadata or {}
import sys

# Ensure project root and app package are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
for candidate in (project_root, app_dir):
    if candidate and candidate not in sys.path:
        sys.path.insert(0, candidate)

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

from common.chroma_db_settings import Chroma, invalidate_sources_cache
from common.embeddings_manager import get_embeddings_manager
from common.chroma_utils import add_langchain_documents, _make_metadata_serializable

# Custom security exception
class SecurityError(Exception):
    """Excepción lanzada cuando se detecta una amenaza de seguridad."""
    pass


try:
    from common.chroma_db_settings import get_unique_sources_df as _get_unique_sources_df
except (ImportError, AttributeError):  # pragma: no cover - fallback for lightweight stubs
    def _get_unique_sources_df(chroma_settings) -> pd.DataFrame:  # type: ignore
        logger.warning("Using fallback get_unique_sources_df function - ChromaDB settings not available")
        return pd.DataFrame(data=None, columns=["uploaded_file_name", "domain", "collection"])
from common.constants import CHROMA_SETTINGS
from common.text_normalization import Document, normalize_documents_nfc
from common.privacy import PrivacyManager

get_unique_sources_df = _get_unique_sources_df

logger = logging.getLogger(__name__)



def _safe_streamlit_call(name: str, *args, **kwargs) -> None:
    """Invoke a Streamlit UI helper, ignoring missing script context."""

    fn = getattr(st, name, None)
    if not callable(fn):
        return
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # RuntimeError when ScriptRunContext is missing
        logger.debug("Streamlit call %s suppressed: %s", name, exc)



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
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
CHROMA_BATCH_SIZE = 64


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
    kwargs = {
        "chunk_size": config["chunk_size"],
        "chunk_overlap": config["chunk_overlap"],
    }
    separators = config.get("separators", ["\n\n", "\n", " "])
    kwargs["separators"] = separators

    try:
        return RecursiveCharacterTextSplitter(**kwargs)
    except TypeError:
        kwargs.pop("separators", None)
        splitter = RecursiveCharacterTextSplitter(**kwargs)
        if hasattr(splitter, "separators"):
            splitter.separators = separators
        return splitter


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


def _load_documents(uploaded_file, file_name: str) -> Tuple[List[Any], BaseFileIngestor]:
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    ingestor = _get_ingestor_for_extension(ext)

    if ingestor is None:
        raise ValueError(f"No ingestor found for extension: {ext}")

    try:
        with _temp_file(uploaded_file) as tmp_path:
            try:
                documents = ingestor.load(tmp_path, ext)
            except TypeError as exc:
                logger.debug(
                    "Loader %s failed for %s: %s - falling back to plain reader",
                    ingestor.__class__.__name__,
                    file_name,
                    exc,
                )
                try:
                    with open(tmp_path, 'r', encoding='utf-8') as handle:
                        fallback_content = handle.read()
                except UnicodeDecodeError:
                    with open(tmp_path, 'r', encoding='latin-1', errors='ignore') as handle:
                        fallback_content = handle.read()
                fallback_metadata = {"source": tmp_path}
                try:
                    documents = [Document(page_content=fallback_content, metadata=fallback_metadata)]
                except (TypeError, NameError) as doc_error:
                    # Try to handle missing Document class or initialization issues
                    logger.debug(
                        "Document class failed for %s: %s - using LangChain Document",
                        file_name,
                        doc_error,
                    )
                    # Use LangChain Document as fallback
                    documents = [LangChainDocument(page_content=fallback_content, metadata=fallback_metadata)]

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
            try:
                document.metadata = _make_metadata_serializable(metadata)
            except TypeError as exc:
                raise TypeError(
                    f"Cannot update metadata for document type {type(document)}: {exc}"
                ) from exc

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

    def to_summary(self) -> Dict[str, Any]:
        """Return a JSON-serialisable summary of the processed result."""

        chunk_count = len(self._documents)
        total_characters = 0
        collected_warnings: set[str] = set()

        for document in self._documents:
            content = getattr(document, "page_content", "")
            if isinstance(content, str):
                total_characters += len(content)

            metadata = getattr(document, "metadata", None)
            if isinstance(metadata, dict):
                warnings = metadata.get("warnings")
                if isinstance(warnings, str):
                    collected_warnings.add(warnings)
                elif isinstance(warnings, (list, tuple, set)):
                    for item in warnings:
                        if isinstance(item, str):
                            collected_warnings.add(item)

        summary: Dict[str, Any] = {
            "domain": getattr(self.ingestor, "domain", None),
            "collection": getattr(self.ingestor, "collection_name", None),
            "duplicate": self.duplicate,
            "chunk_count": chunk_count,
            "total_characters": total_characters,
        }

        if collected_warnings:
            summary["warnings"] = sorted(collected_warnings)

        return summary


def _collection_contains_file(collection, file_name: str) -> bool:
    # Check if collection is None
    if collection is None:
        logger.error(f"Collection is None for file {file_name}")
        return False

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
        return False, "Archivo demasiado grande (máximo 200MB)"

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
        reset_pointer = hasattr(uploaded_file, "seek")
        if hasattr(uploaded_file, "read"):
            file_bytes = uploaded_file.read()
        elif hasattr(uploaded_file, "getvalue"):
            file_bytes = uploaded_file.getvalue()
        else:
            raise AttributeError("Uploaded file object does not support reading")

        # Guardar archivo temporalmente para escaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            # Escanear archivo por amenazas
            scan_result = scan_file_for_conversion(temp_file_path)

            if not scan_result.is_safe:
                # Archivo peligroso detectado
                threat_msg = f"🚨 ARCHIVO BLOQUEADO: {file_name}"
                security_msg = f"Nivel de amenaza: {scan_result.threat_level.upper()}"
                threats_msg = "Amenazas detectadas: " + ", ".join(scan_result.threats_detected)

                _safe_streamlit_call("error", threat_msg)
                _safe_streamlit_call("error", security_msg)
                _safe_streamlit_call("error", threats_msg)

                if scan_result.quarantine_path:
                    _safe_streamlit_call("warning", f"Archivo puesto en cuarentena: {scan_result.quarantine_path}")

                logger.error(f"Archivo bloqueado por seguridad: {file_name} - {scan_result.threat_level}")
                logger.error(f"Amenazas: {scan_result.threats_detected}")

                # Retornar resultado vacío para bloquear procesamiento
                raise SecurityError(f"Archivo bloqueado por seguridad: {scan_result.threat_level}")

            else:
                # Archivo seguro
                _safe_streamlit_call("success", f"✅ Archivo seguro: {file_name}")
                logger.info(f"Archivo aprobado por seguridad: {file_name}")

                # Resetear el puntero del archivo para procesamiento normal
                if reset_pointer and hasattr(uploaded_file, "seek"):
                    uploaded_file.seek(0)

        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    else:
        # Escaneo deshabilitado - mostrar advertencia
        _safe_streamlit_call("warning", "⚠️ Escaneo de seguridad deshabilitado - Procesando sin verificación antimalware")
        logger.warning(f"Procesando archivo sin escaneo de seguridad: {file_name}")

    # Continuar con procesamiento normal si el archivo es seguro
    try:
        documents, ingestor = load_single_document(uploaded_file, file_name)
    except Exception as e:
        logger.error(f"Error loading document {file_name}: {e}")
        raise

    try:
        collection = CHROMA_SETTINGS.get_or_create_collection(ingestor.collection_name)
        if collection is None:
            logger.error(f"Failed to create or get collection '{ingestor.collection_name}' for file {file_name}")
            raise ValueError(f"No se pudo crear la colección '{ingestor.collection_name}' para el archivo {file_name}")

        if _collection_contains_file(collection, file_name):
            return ProcessResult([], ingestor, duplicate=True)
    except Exception as e:
        logger.error(f"Error checking collection for file {file_name}: {e}")
        raise ValueError(f"Error de conexión con la base de datos vectorial: {str(e)}")

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
                text.metadata = _make_metadata_serializable(text.metadata)

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
        try:
            response = collection.get(include=["metadatas"])
        except ValueError:
            response = collection.get()
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
    # Archivos < 1MB = prioridad 1, < 100MB = prioridad 2, >= 100MB = prioridad 3
    if file_size < 1024 * 1024:  # < 1MB
        priority = 1
    elif file_size < 100 * 1024 * 1024:  # < 100MB
        priority = 2
    else:  # >= 100MB
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
            summary = result.to_summary()
            if result.duplicate:
                logger.warning("Archivo duplicado: %s", file_name)
                _safe_streamlit_call("warning", f"⚠️ Archivo duplicado: {file_name}")
                summary["duplicate"] = True
                return {
                    "success": False,
                    "error": "Archivo ya existe en la base de datos",
                    "summary": summary,
                    "domain": summary.get("domain"),
                    "collection": summary.get("collection"),
                    "duplicate": True,
                }
            elif hasattr(result, 'documents') and len(result.documents) > 0:
                # Store documents in ChromaDB
                texts = result.documents
                ingestor = result.ingestor
                embeddings = get_embeddings(ingestor.domain)

                from langchain_core.documents import Document as LangChainDocument
                try:
                    langchain_docs = [
                        LangChainDocument(page_content=doc.page_content, metadata=dict(doc.metadata))
                        for doc in texts
                    ]
                except TypeError:
                    # Fallback for lightweight stubs during testing - ensure proper type conversion
                    try:
                        langchain_docs = [
                            LangChainDocument(page_content=doc.page_content, metadata=dict(doc.metadata))
                            for doc in texts
                        ]
                    except (TypeError, AttributeError) as conversion_error:
                        logger.warning(
                            "Unable to convert documents for %s (types: %s): %s - using fallback conversion",
                            file_name,
                            [type(doc) for doc in texts],
                            conversion_error,
                        )
                        # Use the same LangChainDocument class for consistency
                        langchain_docs = [
                            LangChainDocument(
                                page_content=doc.page_content,
                                metadata=dict(getattr(doc, 'metadata', {})),
                            )
                            for doc in texts
                        ]

                collection_ref = locals().get('collection')
                if collection_ref is None:
                    collection_ref = CHROMA_SETTINGS.get_or_create_collection(ingestor.collection_name)

                try:
                    if hasattr(collection_ref, 'add'):
                        existed, added = add_langchain_documents(
                            CHROMA_SETTINGS,
                            ingestor.collection_name,
                            embeddings,
                            langchain_docs,
                            batch_size=CHROMA_BATCH_SIZE,
                        )
                    else:
                        try:
                            preexisting = collection_ref.count()
                        except Exception:
                            preexisting = 0
                        vector_store = Chroma(
                            collection_name=ingestor.collection_name,
                            embedding_function=embeddings,
                            client=CHROMA_SETTINGS,
                        )
                        vector_store.add_documents(langchain_docs)
                        existed = preexisting > 0
                        added = len(langchain_docs)
                except Exception as storage_error:
                    logger.error(f"Error al almacenar documentos en ChromaDB para {file_name}: {storage_error}")
                    return {"success": False, "error": f"Error al almacenar en base de datos: {str(storage_error)}"}

                if not existed:
                    _safe_streamlit_call("info", "Creando nueva base de datos vectorial...")
                logger.info("Colección '%s' recibió %s documentos (existía=%s)", ingestor.collection_name, added, existed)

                _safe_streamlit_call("success", f"Se agregó el archivo '{file_name}' con éxito.")
                invalidate_sources_cache()
                return {
                    "success": True,
                    "message": f"Archivo procesado y almacenado con {len(result.documents)} documentos",
                    "domain": ingestor.domain,
                    "collection": ingestor.collection_name,
                    "summary": summary,
                }
            else:
                logger.error("No se generaron documentos para el archivo: %s", file_name)
                return {"success": False, "error": "No se generaron documentos válidos"}
        else:
            # If it's already a dict, return as is
            return result
    except Exception as e:
        logger.error("Error durante la ingesta del archivo %s: %s", file_name, str(e))
        error_msg = str(e)

        # Provide more specific error messages based on the error type
        if "conexión" in error_msg.lower() or "connection" in error_msg.lower():
            error_msg = "Error de conexión con la base de datos vectorial. Verifique que ChromaDB esté ejecutándose."
        elif "colección" in error_msg.lower() or "collection" in error_msg.lower():
            error_msg = "Error al acceder a la colección de la base de datos vectorial."
        elif "NoneType" in error_msg and "get" in error_msg:
            error_msg = "Error interno: problema con la configuración de la base de datos vectorial."
        elif "security" in error_msg.lower():
            error_msg = f"Archivo bloqueado por seguridad: {error_msg}"

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
            _safe_streamlit_call("warning", "Este archivo ya fue agregado anteriormente.")
            logger.warning("Archivo duplicado: %s", file_name)
            return

        texts = result.documents
        ingestor = result.ingestor
        embeddings = get_embeddings(ingestor.domain)

        from langchain_core.documents import Document as LangChainDocument
        langchain_docs = [
            LangChainDocument(page_content=doc.page_content, metadata=dict(doc.metadata))
            for doc in texts
        ]

        existed, added = add_langchain_documents(
            CHROMA_SETTINGS,
            ingestor.collection_name,
            embeddings,
            langchain_docs,
            batch_size=CHROMA_BATCH_SIZE,
        )
        if not existed:
            _safe_streamlit_call("info", "Creando nueva base de datos vectorial...")
        logger.info("Colección '%s' recibió %s documentos (existía=%s)", ingestor.collection_name, added, existed)

        _safe_streamlit_call("success", f"Se agregó el archivo '{file_name}' con éxito.")
        logger.info("Archivo procesado exitosamente: %s", file_name)

    except SecurityError as sec_exc:
        # Manejo específico de errores de seguridad
        security_msg = f"🚨 ARCHIVO BLOQUEADO POR SEGURIDAD: '{file_name}'"
        _safe_streamlit_call("error", security_msg)
        _safe_streamlit_call("error", f"Motivo: {sec_exc}")
        _safe_streamlit_call("warning", "El archivo no fue procesado por razones de seguridad.")
        logger.error("Archivo bloqueado por seguridad: %s - %s", file_name, sec_exc)
        return  # No continuar procesamiento

    except Exception as exc:
        error_msg = f"Error al procesar el archivo '{file_name}': {exc}"
        _safe_streamlit_call("error", error_msg)
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
    invalidate_sources_cache()
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



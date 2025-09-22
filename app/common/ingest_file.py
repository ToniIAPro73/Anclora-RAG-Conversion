"""Utilities to ingest files into the vector database."""
from __future__ import annotations

import logging
import os
import tempfile
import uuid
from contextlib import contextmanager
from threading import Lock
from typing import List, Tuple, Optional

import pandas as pd
import streamlit as st
# Provide a lightweight fallback when ``langchain`` is not available during tests.
try:  # pragma: no cover - prefer the real implementation when installed
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
except Exception:  # pragma: no cover - fallback path used in constrained environments
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        """Minimal splitter that returns documents unchanged."""

        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 0) -> None:  # noqa: D401
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_documents(self, documents):
            return list(documents)
from langchain_community.embeddings import HuggingFaceEmbeddings

from ..agents import (
    BaseFileIngestor,
    CodeIngestor,
    DocumentIngestor,
    MultimediaIngestor,
    refresh_document_loaders,
)
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from common.chroma_db_settings import Chroma

try:
    from common.chroma_db_settings import get_unique_sources_df as _get_unique_sources_df
except (ImportError, AttributeError):  # pragma: no cover - fallback for lightweight stubs
    def _get_unique_sources_df(_chroma_settings) -> pd.DataFrame:
        return pd.DataFrame(columns=["uploaded_file_name", "domain", "collection"])
from common.constants import CHROMA_SETTINGS
from common.text_normalization import Document, normalize_documents_nfc
from common.privacy import PrivacyManager

get_unique_sources_df = _get_unique_sources_df

logger = logging.getLogger(__name__)


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

# Load environment variables
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")

_embeddings_lock: Lock = Lock()
_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached instance of the embeddings model."""

    global _embeddings_instance
    if _embeddings_instance is None:
        with _embeddings_lock:
            if _embeddings_instance is None:
                _embeddings_instance = HuggingFaceEmbeddings(
                    model_name=embeddings_model_name
                )
    return _embeddings_instance

# Ensure the ingestors see the latest loader implementations when the module is re-imported
refresh_document_loaders(force=True)

INGESTORS: Tuple[BaseFileIngestor, ...] = (
    DocumentIngestor,
    CodeIngestor,
    MultimediaIngestor,
)

SUPPORTED_EXTENSIONS = sorted({ext for ingestor in INGESTORS for ext in ingestor.extensions})


def _get_ingestor_for_extension(extension: str) -> BaseFileIngestor:
    for ingestor in INGESTORS:
        if ingestor.supports_extension(extension):
            return ingestor
    raise ValueError(f"Tipo de archivo no soportado: {extension}")


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

    with _temp_file(uploaded_file) as tmp_path:
        documents = ingestor.load(tmp_path, ext)

    for document in documents:
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
    except Exception:  # pragma: no cover - chroma specific failure fallback
        results = collection.get()
    ids = results.get("ids", []) if isinstance(results, dict) else []
    metadatas = results.get("metadatas", []) if isinstance(results, dict) else []
    if ids:
        return True
    return any(
        metadata and metadata.get("uploaded_file_name") == file_name for metadata in metadatas
    )


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
        return _load_documents(uploaded_file, file_name)
    except Exception as exc:
        logger.error("Error al cargar documento %s: %s", uploaded_file.name, exc)
        raise


def process_file(uploaded_file, file_name: str) -> ProcessResult:
    documents, ingestor = load_single_document(uploaded_file, file_name)
    collection = CHROMA_SETTINGS.get_or_create_collection(ingestor.collection_name)
    if _collection_contains_file(collection, file_name):
        return ProcessResult([], ingestor, duplicate=True)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    texts = text_splitter.split_documents(documents)
    normalized = normalize_documents_nfc(texts)
    return ProcessResult(normalized, ingestor)

def does_vectorstore_exist(settings, collection_name: str) -> bool:
    """Check if a vectorstore already contains data for *collection_name*."""

    collection = settings.get_or_create_collection(collection_name)
    try:
        return collection.count() > 0
    except Exception:  # pragma: no cover - compatibility fallback
        response = collection.get(include=["ids"])
        return bool(response.get("ids"))

def ingest_file(uploaded_file, file_name):
    """Process and ingest a file into the vector database."""

    try:
        logger.info("Iniciando ingesta del archivo: %s", file_name)
        result = process_file(uploaded_file, file_name)

        if result.duplicate:
            st.warning("Este archivo ya fue agregado anteriormente.")
            logger.warning("Archivo duplicado: %s", file_name)
            return

        texts = result.documents
        ingestor = result.ingestor
        embeddings = get_embeddings()

        spinner_message = f"Creando embeddings para {file_name}..."
        if does_vectorstore_exist(CHROMA_SETTINGS, ingestor.collection_name):
            db = Chroma(
                collection_name=ingestor.collection_name,
                embedding_function=embeddings,
                client=CHROMA_SETTINGS,
            )
            with st.spinner(spinner_message):
                db.add_documents(texts)
        else:
            st.info("Creando nueva base de datos vectorial...")
            with st.spinner("Creando embeddings. Esto puede tomar algunos minutos..."):
                try:
                    Chroma.from_documents(
                        texts,
                        embeddings,
                        client=CHROMA_SETTINGS,
                        collection_name=ingestor.collection_name,
                    )
                except TypeError:
                    # Compatibilidad con dobles de prueba minimalistas.
                    Chroma.from_documents(texts, embeddings, CHROMA_SETTINGS)

        st.success(f"Se agregó el archivo '{file_name}' con éxito.")
        logger.info("Archivo procesado exitosamente: %s", file_name)
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

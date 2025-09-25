"""Advanced ingestion system orchestrating multiple input types."""
from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document as LangChainDocument

from app.common.logger import Logger
from app.common.constants import CHROMA_SETTINGS
from app.common.ingest_file import does_vectorstore_exist, get_embeddings
from app.ingestion.config import IngestionConfig, get_ingestion_config
from app.ingestion.file_processor import FileProcessor
from app.ingestion.folder_processor import FolderProcessor
from app.ingestion.markdown_source_parser import MarkdownSourceParser
from app.ingestion.validation_service import ValidationService
from app.ingestion.github_processor import GitHubRepositoryProcessor, RepositoryOptions
from app.common.chroma_db_settings import Chroma


class IngestionStatus(Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class IngestionJob:
    job_id: str
    type: str
    status: IngestionStatus = IngestionStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedIngestionSystem:
    """Coordinator that exposes high level ingestion workflows."""

    def __init__(self, config: Optional[IngestionConfig] = None) -> None:
        self._logger = Logger(__name__)
        self.config = config or get_ingestion_config()
        self.file_processor = FileProcessor()
        self.folder_processor = FolderProcessor()
        self.markdown_parser = MarkdownSourceParser()
        self.validator = ValidationService()
        self.github_processor = GitHubRepositoryProcessor()
        self.supported_formats = self.config.supported_formats
        self.max_file_size = self.config.max_file_size
        self.markdown_collection = self.config.markdown_collection
        self.active_jobs: Dict[str, IngestionJob] = {}
        self._job_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    async def ingest_files(
        self,
        files: List[Any],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionJob:
        job = self._create_job("file", metadata or {"user_id": user_id})
        job.total_files = len(files)
        self._logger.info("Iniciando ingesta de %s archivos para %s", job.total_files, user_id)

        try:
            job.status = IngestionStatus.VALIDATING
            valid_files: List[Dict[str, Any]] = []
            for file_obj in files:
                validation = await self.validator.validate_file(file_obj, self.max_file_size, self.supported_formats)
                if validation["valid"]:
                    valid_files.append({"file": file_obj, "validation": validation})
                else:
                    job.errors.append({
                        "file": getattr(file_obj, "name", "archivo_desconocido"),
                        "error": validation.get("error", "Error de validacion"),
                    })
                    job.failed_files += 1
            if not valid_files:
                job.status = IngestionStatus.FAILED
                return job

            job.status = IngestionStatus.PROCESSING
            for entry in valid_files:
                file_obj = entry["file"]
                validation = entry["validation"]
                file_metadata = {
                    "user_id": user_id,
                    "category": validation.get("category"),
                    "extension": validation.get("extension"),
                    "size": validation.get("size"),
                }
                if metadata:
                    file_metadata.update(metadata)
                try:
                    if hasattr(file_obj, "seek"):
                        file_obj.seek(0)
                    result = await self.file_processor.process_uploaded_file(file_obj, file_metadata)
                    job.files.append(result)
                    if result.get("success"):
                        job.processed_files += 1
                    else:
                        job.failed_files += 1
                        job.errors.append({
                            "file": result.get("file_name"),
                            "error": result.get("error", "Error desconocido"),
                        })
                except Exception as exc:  # pragma: no cover - defensive path
                    self._logger.error("Error procesando archivo %s: %s", getattr(file_obj, "name", "?"), exc)
                    job.failed_files += 1
                    job.errors.append({
                        "file": getattr(file_obj, "name", "archivo_desconocido"),
                        "error": str(exc),
                    })

            job.status = self._final_status(job)
            return job
        finally:
            job.end_time = datetime.now()

    async def ingest_folder(
        self,
        folder_path: str,
        user_id: str,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionJob:
        job = self._create_job("folder", metadata or {"user_id": user_id, "folder": folder_path})
        self._logger.info("Analizando carpeta %s", folder_path)

        try:
            job.status = IngestionStatus.VALIDATING
            discovered = await self.folder_processor.discover_files(
                folder_path,
                self.supported_formats,
                recursive=recursive,
            )
            job.total_files = len(discovered)
            if not discovered:
                job.status = IngestionStatus.COMPLETED
                return job

            job.status = IngestionStatus.PROCESSING
            for file_path in discovered:
                validation = await self.validator.validate_file_path(file_path, self.max_file_size, self.supported_formats)
                if not validation["valid"]:
                    job.failed_files += 1
                    job.errors.append({"file": file_path, "error": validation.get("error")})
                    continue

                file_metadata = {
                    "user_id": user_id,
                    "category": validation.get("category"),
                    "extension": validation.get("extension"),
                    "size": validation.get("size"),
                    "ingest_origin": "folder",
                }
                if metadata:
                    file_metadata.update(metadata)
                try:
                    result = await self.file_processor.process_file_path(file_path, file_metadata)
                    job.files.append(result)
                    if result.get("success"):
                        job.processed_files += 1
                    else:
                        job.failed_files += 1
                        job.errors.append({
                            "file": file_path,
                            "error": result.get("error", "Error desconocido"),
                        })
                except Exception as exc:  # pragma: no cover - defensive path
                    self._logger.error("Error procesando archivo %s: %s", file_path, exc)
                    job.failed_files += 1
                    job.errors.append({"file": file_path, "error": str(exc)})

            job.status = self._final_status(job)
            return job
        finally:
            job.end_time = datetime.now()

    async def ingest_github_repository(
        self,
        repo_url: str,
        user_id: str,
        branch: Optional[str] = None,
        options: Optional[Dict[str, Any] | RepositoryOptions] = None,
        metadata: Optional[Dict[str, Any]] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> IngestionJob:
        """Ingesta un repositorio publico de GitHub en el sistema RAG."""

        additional_metadata = dict(metadata or {})
        additional_metadata.setdefault("user_id", user_id)
        additional_metadata.setdefault("repo_url", repo_url)
        if branch:
            additional_metadata.setdefault("branch", branch)

        job = self._create_job("github_repository", additional_metadata)
        job.status = IngestionStatus.VALIDATING

        repo_path: Optional[str]
        if analysis and analysis.get("temp_path"):
            repo_path = analysis["temp_path"]
        else:
            repo_path = await self.github_processor.clone_repository(repo_url, branch)

        if not repo_path:
            job.status = IngestionStatus.FAILED
            job.errors.append({"general": "No fue posible clonar el repositorio proporcionado."})
            job.end_time = datetime.now()
            return job

        repo_options = self._build_repository_options(options)
        files = await self.github_processor.gather_repository_files(repo_path, repo_options)
        job.total_files = len(files)
        job.status = IngestionStatus.PROCESSING

        if analysis:
            analysis_copy = dict(analysis)
            analysis_copy.pop("temp_path", None)
            job.metadata["analysis"] = analysis_copy

        if not files:
            job.status = IngestionStatus.FAILED
            job.errors.append({"general": "No se encontraron archivos validos en el repositorio."})
            await self.github_processor.cleanup_repository(repo_path)
            job.end_time = datetime.now()
            return job

        commit_hash = self.github_processor.get_commit_hash(repo_path)

        try:
            for file_info in files:
                try:
                    file_obj = self.github_processor.wrap_file(file_info["path"])
                    validation = await self.validator.validate_file(file_obj, self.max_file_size, self.supported_formats)
                    if not validation["valid"]:
                        job.failed_files += 1
                        job.errors.append({
                            "file": file_info["relative_path"],
                            "error": validation.get("error", "Archivo no valido"),
                        })
                        continue

                    file_metadata = {
                        "user_id": user_id,
                        "category": validation.get("category"),
                        "extension": validation.get("extension"),
                        "size": validation.get("size"),
                        "repo_url": repo_url,
                        "repo_branch": branch or "default",
                        "repo_relative_path": file_info["relative_path"],
                        "repo_commit": commit_hash,
                    }
                    if metadata:
                        file_metadata.update(metadata)

                    file_obj.seek(0)
                    result = await self.file_processor.process_uploaded_file(file_obj, file_metadata)
                    job.files.append(result)
                    if result.get("success"):
                        job.processed_files += 1
                    else:
                        if result.get("error") == "Archivo ya existe en la base de datos":
                            job.skipped_files = job.skipped_files + 1 if hasattr(job, 'skipped_files') else 1
                        job.failed_files += 1
                        job.errors.append({
                            "file": file_info["relative_path"],
                            "error": result.get("error", "Error desconocido"),
                        })
                except Exception as exc:  # pragma: no cover - defensive path
                    self._logger.error("Error procesando %s: %s", file_info["relative_path"], exc)
                    job.failed_files += 1
                    job.errors.append({"file": file_info["relative_path"], "error": str(exc)})

            job.status = self._final_status(job)
            return job
        finally:
            await self.github_processor.cleanup_repository(repo_path)
            job.end_time = datetime.now()


    async def ingest_markdown_sources(
        self,
        markdown_content: str,
        user_id: str,
        source_name: str = "markdown_sources",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionJob:
        job = self._create_job("markdown_sources", metadata or {"user_id": user_id, "source_name": source_name})
        job.status = IngestionStatus.VALIDATING

        try:
            validation = await self.markdown_parser.validate_source_format(markdown_content)
            if not validation["valid"]:
                job.status = IngestionStatus.FAILED
                job.errors.append({"source": source_name, "error": "; ".join(validation["errors"])})
                return job

            sources = await self.markdown_parser.parse_sources(markdown_content)
            job.total_files = len(sources)
            if not sources:
                job.status = IngestionStatus.FAILED
                job.errors.append({"source": source_name, "error": "No se encontraron fuentes validas"})
                return job

            job.status = IngestionStatus.INDEXING
            for source in sources:
                try:
                    document = self._build_document_from_source(source, source_name, user_id)
                    indexing_result = await self._index_document(document)
                    job.files.append(indexing_result)
                    job.processed_files += 1
                except Exception as exc:  # pragma: no cover - defensive path
                    self._logger.error("Error indexando fuente %s: %s", source.get("id"), exc)
                    job.failed_files += 1
                    job.errors.append({"source": source.get("id"), "error": str(exc)})

            job.status = self._final_status(job)
            return job
        finally:
            job.end_time = datetime.now()

    # ------------------------------------------------------------------
    def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        return self.active_jobs.get(job_id)

    def get_user_jobs(self, user_id: str) -> List[IngestionJob]:
        return [job for job in self.active_jobs.values() if job.metadata.get("user_id") == user_id]

    async def cancel_job(self, job_id: str) -> bool:
        async with self._job_lock:
            job = self.active_jobs.get(job_id)
            if not job:
                return False
            if job.status in {IngestionStatus.COMPLETED, IngestionStatus.FAILED}:
                return False
            job.status = IngestionStatus.FAILED
            job.errors.append({"general": "Cancelado por el usuario"})
            job.end_time = datetime.now()
            return True

    def _build_repository_options(
        self, options: Optional[Dict[str, Any] | RepositoryOptions]
    ) -> RepositoryOptions:
        if isinstance(options, RepositoryOptions):
            result = options
        elif options is None:
            result = RepositoryOptions()
        else:
            allowed = {field.name for field in fields(RepositoryOptions)}
            filtered = {key: value for key, value in options.items() if key in allowed}
            result = RepositoryOptions(**filtered)

        if result.allowed_extensions:
            normalised = []
            for ext in result.allowed_extensions:
                ext = ext.lower()
                if not ext.startswith("."):
                    ext = f".{ext}"
                normalised.append(ext)
            result.allowed_extensions = normalised
        return result

    def get_statistics(self) -> Dict[str, Any]:
        jobs = list(self.active_jobs.values())
        total_jobs = len(jobs)
        processed_files = sum(job.processed_files for job in jobs)
        total_files = sum(job.total_files for job in jobs)
        failed_files = sum(job.failed_files for job in jobs)
        completed_jobs = sum(1 for job in jobs if job.status == IngestionStatus.COMPLETED)
        failed_jobs = sum(1 for job in jobs if job.status == IngestionStatus.FAILED)
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_files": total_files,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "success_rate": (processed_files / total_files * 100) if total_files else 0,
        }

    # ------------------------------------------------------------------
    def _create_job(self, job_type: str, metadata: Dict[str, Any]) -> IngestionJob:
        job_id = self._generate_job_id(metadata.get("user_id", "anonymous"), job_type)
        job = IngestionJob(job_id=job_id, type=job_type, metadata=dict(metadata))
        self.active_jobs[job_id] = job
        return job

    def _generate_job_id(self, user_id: str, job_type: str) -> str:
        payload = f"{user_id}-{job_type}-{datetime.utcnow().isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _final_status(self, job: IngestionJob) -> IngestionStatus:
        if job.processed_files == job.total_files:
            return IngestionStatus.COMPLETED
        if job.processed_files == 0:
            return IngestionStatus.FAILED
        return IngestionStatus.PARTIALLY_COMPLETED

    def _build_document_from_source(
        self,
        source: Dict[str, Any],
        source_document: str,
        user_id: str,
    ) -> Dict[str, Any]:
        content = (
            f"# Fuente: {source.get('id', 'Sin ID')}\n\n"
            f"Tipo: {source.get('type', 'N/A')}\n"
            f"Titulo: {source.get('title', 'N/A')}\n"
            f"Autores: {source.get('authors', 'N/A')}\n"
            f"Origen: {source.get('publisher', 'N/A')}\n"
            f"Anio: {source.get('year', 'N/A')}\n"
            f"URL o DOI: {source.get('url', 'N/A')}\n"
            f"Citacion: {source.get('citation', 'N/A')}\n"
            f"Documento Fuente: {source_document}\n\n"
            f"## Contenido adicional\n{source.get('additional_content', '').strip()}\n"
        )
        metadata = {
            "source_id": source.get("id"),
            "source_type": source.get("type"),
            "title": source.get("title"),
            "authors": source.get("authors"),
            "year": source.get("year"),
            "user_id": user_id,
            "collection": self.markdown_collection,
            "domain": "references",
        }
        return {"content": content, "metadata": metadata}

    async def _index_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        embeddings = get_embeddings("documents")
        langchain_doc = LangChainDocument(page_content=document["content"], metadata=document["metadata"])
        collection_name = self.markdown_collection
        if does_vectorstore_exist(CHROMA_SETTINGS, collection_name):
            db = Chroma(collection_name=collection_name, embedding_function=embeddings, client=CHROMA_SETTINGS)
            db.add_documents([langchain_doc])
        else:
            Chroma.from_documents([langchain_doc], embeddings, client=CHROMA_SETTINGS, collection_name=collection_name)
        return {
            "document_id": document["metadata"].get("source_id"),
            "status": "indexed",
            "collection": collection_name,
        }


__all__ = ["AdvancedIngestionSystem", "IngestionStatus", "IngestionJob"]

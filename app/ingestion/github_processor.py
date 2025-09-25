"""GitHub repository ingestion helpers."""
from __future__ import annotations

import asyncio
import io
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from fnmatch2 import fnmatchcase  # type: ignore
except Exception:  # pragma: no cover - fallback to stdlib
    from fnmatch import fnmatchcase  # type: ignore

from app.common.logger import Logger

try:  # pragma: no cover - optional dependency
    from git import Repo, GitCommandError  # type: ignore
except Exception:  # pragma: no cover - provide graceful fallback
    Repo = None
    GitCommandError = Exception


@dataclass
class RepositoryOptions:
    """Options controlling repository processing."""

    include_docs: bool = True
    include_code: bool = True
    include_media: bool = False
    include_other: bool = False
    max_file_size_mb: int = 25
    allowed_extensions: Optional[Iterable[str]] = None


class GitHubRepositoryProcessor:
    """Clone, analyse and enumerate files from a public GitHub repository."""

    _DEFAULT_IGNORED_DIRS = {
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        ".git",
        ".github",
        ".venv",
        "venv",
        "env",
        ".idea",
        ".vscode",
        "coverage",
    }

    _DEFAULT_IGNORED_PATTERNS = {
        "*.lock",
        "*.log",
        "*.tmp",
        "*.pyc",
        "*.pyo",
        "*.so",
    }

    def __init__(self) -> None:
        self._logger = Logger(__name__)

    async def analyze_repository(
        self,
        repo_url: str,
        branch: Optional[str],
        options: Optional[RepositoryOptions] = None,
    ) -> Dict[str, Any]:
        """Clone the repository and return statistics for UI presentation."""

        cloned_path = await self.clone_repository(repo_url, branch)
        if not cloned_path:
            return {
                "success": False,
                "error": "No fue posible clonar el repositorio. Verifica la URL y que sea publico.",
            }

        opts = options or RepositoryOptions()
        files = await self.gather_repository_files(cloned_path, opts)
        total_size = sum(item["size"] for item in files)

        summary = {
            "success": True,
            "repository": repo_url,
            "branch": branch or "default",
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_extension": self._summarise_by_extension(files),
            "temp_path": cloned_path,
        }
        return summary

    async def clone_repository(self, repo_url: str, branch: Optional[str]) -> Optional[str]:
        """Clone *repo_url* to a temporary location and return the path."""

        if Repo is None:  # pragma: no cover - dependency missing
            self._logger.error("GitPython no esta instalado. Ejecuta 'pip install GitPython'.")
            return None

        target_dir = tempfile.mkdtemp(prefix="anclora_repo_")
        try:
            clone_args = {"depth": 1}
            if branch:
                clone_args["branch"] = branch
            Repo.clone_from(repo_url, target_dir, **clone_args)
            self._logger.info("Repositorio clonado en %s", target_dir)
            return target_dir
        except GitCommandError as exc:  # pragma: no cover - network dependent
            self._logger.error("Error clonando repositorio %s: %s", repo_url, exc)
            shutil.rmtree(target_dir, ignore_errors=True)
            return None
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.error("Fallo inesperado clonando %s: %s", repo_url, exc)
            shutil.rmtree(target_dir, ignore_errors=True)
            return None

    async def gather_repository_files(
        self,
        repo_path: str,
        options: RepositoryOptions,
    ) -> List[Dict[str, Any]]:
        """Return repository files that satisfy the filtering options."""

        return await asyncio.to_thread(self._gather_repository_files_sync, repo_path, options)

    async def cleanup_repository(self, repo_path: str) -> None:
        """Remove a previously cloned repository."""

        await asyncio.to_thread(shutil.rmtree, repo_path, True)

    # ------------------------------------------------------------------
    def get_commit_hash(self, repo_path: str) -> Optional[str]:
        """Return the HEAD commit hash if available."""

        if Repo is None:  # pragma: no cover - dependency missing
            return None
        try:
            repository = Repo(repo_path)
            return repository.head.commit.hexsha
        except Exception:
            return None

    def _gather_repository_files_sync(
        self,
        repo_path: str,
        options: RepositoryOptions,
    ) -> List[Dict[str, Any]]:
        base = Path(repo_path)
        candidates: List[Dict[str, Any]] = []
        allowed_exts = set(options.allowed_extensions or [])
        size_limit = options.max_file_size_mb * 1024 * 1024

        for path in base.rglob("*"):
            relative = path.relative_to(base)
            relative_parts = relative.parts
            relative_str = str(relative).replace(os.sep, "/")

            if path.is_dir():
                if path.name in self._DEFAULT_IGNORED_DIRS or any(part in self._DEFAULT_IGNORED_DIRS for part in relative_parts):
                    continue
                continue

            if any(part in self._DEFAULT_IGNORED_DIRS for part in relative_parts):
                continue

            if any(fnmatchcase(path.name, pattern) or fnmatchcase(relative_str, pattern) for pattern in self._DEFAULT_IGNORED_PATTERNS):
                continue

            try:
                size = path.stat().st_size
            except OSError:
                continue

            if size == 0 or size > size_limit:
                continue

            extension = path.suffix.lower()
            category = self._category_for_extension(extension)
            if not self._should_include(category, extension, options, allowed_exts):
                continue

            candidates.append(
                {
                    "path": path,
                    "relative_path": relative_str,
                    "extension": extension,
                    "size": size,
                    "category": category,
                }
            )

        return candidates

    def _should_include(
        self,
        category: str,
        extension: str,
        options: RepositoryOptions,
        allowed_exts: set[str],
    ) -> bool:
        if allowed_exts and extension not in allowed_exts:
            return False

        if category == "documents":
            return options.include_docs
        if category == "code":
            return options.include_code
        if category == "images":
            return options.include_media
        return options.include_other

    def _category_for_extension(self, extension: str) -> str:
        if extension in {".md", ".rst", ".txt", ".pdf", ".docx"}:
            return "documents"
        if extension in {".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".swift", ".kt"}:
            return "code"
        if extension in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            return "images"
        return "other"

    def _summarise_by_extension(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for item in files:
            summary[item["extension"]] = summary.get(item["extension"], 0) + 1
        return summary

    def wrap_file(self, file_path: Path) -> Any:
        """Return an in-memory file-like object compatible with the ingestion pipeline."""

        data = file_path.read_bytes()
        return _InMemoryFile(data, file_path.name)


class _InMemoryFile:
    """Streamlit-style uploaded file backed by memory."""

    def __init__(self, data: bytes, name: str) -> None:
        self._buffer = io.BytesIO(data)
        self.name = name
        self.size = len(data)

    def read(self, size: int | None = None) -> bytes:
        return self._buffer.read() if size is None else self._buffer.read(size)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        return self._buffer.seek(offset, whence)

    def tell(self) -> int:
        return self._buffer.tell()

    def getvalue(self) -> bytes:
        return self._buffer.getvalue()


__all__ = ["GitHubRepositoryProcessor", "RepositoryOptions"]

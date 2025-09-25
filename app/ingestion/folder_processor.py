"""Folder discovery utilities for the advanced ingestion flow."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from app.common.logger import Logger


class FolderProcessor:
    """Discover and analyse files stored in local folders."""

    def __init__(self) -> None:
        self._logger = Logger(__name__)
        self._ignored_folders = {
            "__pycache__",
            ".git",
            ".svn",
            "node_modules",
            ".idea",
            ".vscode",
            "venv",
            "env",
            ".env",
        }
        self._ignored_files = {".DS_Store", "Thumbs.db", "desktop.ini"}

    async def discover_files(
        self,
        folder_path: str,
        supported_formats: Dict[str, Iterable[str]],
        recursive: bool = True,
        max_depth: int = 10,
    ) -> List[str]:
        """Return a list of discoverable files matching the supported formats."""

        return await asyncio.to_thread(
            self._discover_sync,
            folder_path,
            supported_formats,
            recursive,
            max_depth,
        )

    async def analyze_folder_structure(self, folder_path: str) -> Dict[str, object]:
        """Return light analytics about the target folder."""

        return await asyncio.to_thread(self._analyze_sync, folder_path)

    async def create_folder_report(
        self,
        folder_path: str,
        supported_formats: Dict[str, Iterable[str]],
    ) -> Dict[str, object]:
        """Produce an analysis report combining discovery and statistics."""

        files, structure = await asyncio.gather(
            self.discover_files(folder_path, supported_formats),
            self.analyze_folder_structure(folder_path),
        )

        categorized = self._categorize(files, supported_formats)
        return {
            "folder_info": structure,
            "discovered_files": {
                "total": len(files),
                "by_category": {key: len(items) for key, items in categorized.items()},
                "details": categorized,
            },
            "recommendations": self._build_recommendations(structure, categorized),
        }

    # ------------------------------------------------------------------
    def _discover_sync(
        self,
        folder_path: str,
        supported_formats: Dict[str, Iterable[str]],
        recursive: bool,
        max_depth: int,
    ) -> List[str]:
        path = Path(folder_path)
        if not path.exists():
            raise ValueError(f"La carpeta no existe: {folder_path}")
        if not path.is_dir():
            raise ValueError(f"La ruta no es una carpeta: {folder_path}")

        valid_extensions = {ext for extensions in supported_formats.values() for ext in extensions}

        def walk(directory: Path, depth: int) -> List[str]:
            collected: List[str] = []
            if depth > max_depth:
                self._logger.warning("Profundidad maxima alcanzada en %s", directory)
                return collected
            try:
                for item in directory.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.is_file():
                        if item.name in self._ignored_files:
                            continue
                        if item.suffix.lower() in valid_extensions:
                            collected.append(str(item.resolve()))
                    elif recursive and item.is_dir():
                        if item.name in self._ignored_folders:
                            continue
                        collected.extend(walk(item, depth + 1))
            except PermissionError:
                self._logger.warning("Sin permisos para acceder a %s", directory)
            return collected

        discovered = walk(path, 0)
        self._logger.info("Descubiertos %s archivos validos en %s", len(discovered), folder_path)
        return discovered

    def _analyze_sync(self, folder_path: str) -> Dict[str, object]:
        path = Path(folder_path)
        if not path.exists():
            raise ValueError(f"La carpeta no existe: {folder_path}")
        if not path.is_dir():
            raise ValueError(f"La ruta no es una carpeta: {folder_path}")

        structure = {
            "path": str(path.resolve()),
            "name": path.name,
            "total_size": 0,
            "file_count": 0,
            "folder_count": 0,
            "file_types": {},
            "largest_files": [],
            "tree_structure": {},
        }

        def build_tree(directory: Path, max_depth: int = 3, depth: int = 0):
            if depth >= max_depth:
                return {"...": "max depth reached"}
            tree: Dict[str, object] = {}
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        size = item.stat().st_size
                        tree[item.name] = self._format_size(size)
                        structure["file_count"] += 1
                        structure["total_size"] += size
                        ext = item.suffix.lower()
                        counts = structure["file_types"].setdefault(ext, 0)
                        structure["file_types"][ext] = counts + 1
                        structure["largest_files"].append({
                            "name": item.name,
                            "path": str(item.resolve()),
                            "size": size,
                        })
                    elif item.is_dir() and item.name not in self._ignored_folders:
                        structure["folder_count"] += 1
                        tree[f"{item.name}/"] = build_tree(item, max_depth, depth + 1)
            except PermissionError:
                tree["<sin permisos>"] = None
            return tree

        structure["tree_structure"] = build_tree(path)
        structure["largest_files"].sort(key=lambda entry: entry["size"], reverse=True)
        structure["largest_files"] = structure["largest_files"][:10]
        structure["total_size_formatted"] = self._format_size(structure["total_size"])
        return structure

    def _categorize(self, files: List[str], supported_formats: Dict[str, Iterable[str]]) -> Dict[str, List[Dict[str, str]]]:
        buckets: Dict[str, List[Dict[str, str]]] = {
            "documents": [],
            "images": [],
            "code": [],
            "multimedia": [],
            "archives": [],
            "other": [],
        }
        for file_path in files:
            extension = os.path.splitext(file_path)[1].lower()
            assigned = False
            for category, extensions in supported_formats.items():
                if extension in set(extensions):
                    buckets.setdefault(category, []).append(
                        {"name": os.path.basename(file_path), "path": file_path, "extension": extension}
                    )
                    assigned = True
                    break
            if not assigned:
                buckets["other"].append({"name": os.path.basename(file_path), "path": file_path, "extension": extension})
        return buckets

    def _build_recommendations(self, structure: Dict[str, object], categorized: Dict[str, List[Dict[str, str]]]) -> List[str]:
        recommendations: List[str] = []
        total_size = int(structure.get("total_size", 0))
        file_count = sum(len(items) for items in categorized.values())

        if total_size > 1024 * 1024 * 1024:
            recommendations.append("La carpeta contiene mas de 1GB; considera procesar en lotes.")
        if file_count > 100:
            recommendations.append(
                f"Se detectaron {file_count} archivos. El procesamiento podria tardar mas de lo habitual."
            )
        largest = structure.get("largest_files", [])
        if largest:
            entry = largest[0]
            if entry.get("size", 0) > 200 * 1024 * 1024:
                recommendations.append(
                    f"{entry.get('name')} excede el limite de 200MB y sera omitido durante la ingesta."
                )
        if categorized.get("images") and len(categorized["images"]) > file_count * 0.5:
            recommendations.append("Predominan las imagenes; activa OCR si esperas texto embebido.")
        if categorized.get("code") and len(categorized["code"]) > file_count * 0.3:
            recommendations.append("Se detectan multiples archivos de codigo; se aplicara el agente especializado.")
        return recommendations

    def _format_size(self, size_bytes: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size_bytes)
        for unit in units:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0
        return f"{value:.2f} PB"


__all__ = ["FolderProcessor"]

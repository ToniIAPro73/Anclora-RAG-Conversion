"""Reusable UI helpers for the advanced ingestion Streamlit page."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


@dataclass
class FileUploader:
    """Render a consistent file uploader widget."""

    label: str = "Carga de archivos"

    def render(self, supported_formats: Dict[str, Iterable[str]]) -> List[Any]:
        extensions = sorted({ext.lstrip('.') for values in supported_formats.values() for ext in values})
        files = st.file_uploader(
            self.label,
            accept_multiple_files=True,
            type=extensions,
            help="Selecciona uno o varios archivos para iniciar la ingesta",
        )
        return list(files or [])


@dataclass
class FolderSelector:
    """Render folder selection controls."""

    def render(self) -> Dict[str, Any]:
        folder_path = st.text_input("Ruta de la carpeta", placeholder="/ruta/a/carpeta")
        recursive = st.checkbox("Incluir subcarpetas", value=True)
        analyze = st.button("Analizar carpeta")
        return {"folder_path": folder_path, "recursive": recursive, "analyze": analyze}



@dataclass
class GitHubRepositoryForm:
    """Render controls for GitHub repository ingestion."""

    def render(self) -> Dict[str, Any]:
        with st.form("github_repo_form"):
            repo_url = st.text_input("URL del repositorio", placeholder="https://github.com/organizacion/proyecto")
            branch = st.text_input("Branch", value="main")
            col1, col2 = st.columns(2)
            with col1:
                include_docs = st.checkbox("Incluir documentos", value=True)
                include_media = st.checkbox("Incluir imagenes", value=False)
            with col2:
                include_code = st.checkbox("Incluir codigo", value=True)
                include_other = st.checkbox("Incluir otros archivos", value=False)
            max_file_size_mb = st.number_input("Tamano maximo por archivo (MB)", min_value=1, max_value=200, value=25)
            extensions_text = st.text_input("Extensiones especificas (opcional, separadas por coma)")
            analyze = st.form_submit_button("Analizar repositorio")
            ingest = st.form_submit_button("Procesar repositorio", type="primary")

        allowed_extensions: Optional[List[str]] = None
        if extensions_text.strip():
            allowed_extensions = [f".{ext.strip().lstrip('.')}" for ext in extensions_text.split(',') if ext.strip()]

        options = {
            "include_docs": include_docs,
            "include_code": include_code,
            "include_media": include_media,
            "include_other": include_other,
            "max_file_size_mb": int(max_file_size_mb),
            "allowed_extensions": allowed_extensions,
        }

        return {
            "repo_url": repo_url.strip(),
            "branch": branch.strip(),
            "options": options,
            "analyze": analyze,
            "ingest": ingest,
        }


@dataclass
class MarkdownEditor:
    """Render textarea for markdown based sources."""

    def render(self, default_text: str = "") -> Dict[str, Any]:
        content = st.text_area("Markdown de fuentes", value=default_text, height=300)
        col1, col2 = st.columns(2)
        with col1:
            ingest = st.button("Procesar Markdown", use_container_width=True)
        with col2:
            preview = st.button("Validar formato", use_container_width=True)
        return {"content": content, "ingest": ingest, "preview": preview}


class JobMonitor:
    """Display a table with the latest ingestion jobs."""

    @staticmethod
    def render(jobs: List[Dict[str, Any]]) -> None:
        if not jobs:
            st.info("No hay trabajos registrados para el usuario actual.")
            return
        records = []
        for job in jobs:
            records.append(
                {
                    "Trabajo": job.get("job_id"),
                    "Tipo": job.get("type"),
                    "Estado": job.get("status").value if job.get("status") else "?",
                    "Total": job.get("total_files", 0),
                    "Procesados": job.get("processed_files", 0),
                    "Fallidos": job.get("failed_files", 0),
                    "Inicio": JobMonitor._format_datetime(job.get("start_time")),
                    "Fin": JobMonitor._format_datetime(job.get("end_time")),
                }
            )
        df = pd.DataFrame.from_records(records)
        st.dataframe(df, use_container_width=True)

    @staticmethod
    def _format_datetime(value: Optional[datetime]) -> str:
        if not value:
            return "-"
        return value.strftime("%Y-%m-%d %H:%M:%S")


class StatisticsDisplay:
    """Render high level ingestion statistics."""

    @staticmethod
    def render(stats: Dict[str, Any]) -> None:
        if not stats:
            st.info("Sin estadisticas disponibles.")
            return
        col1, col2, col3 = st.columns(3)
        col1.metric("Trabajos", stats.get("total_jobs", 0))
        col2.metric("Completados", stats.get("completed_jobs", 0))
        col3.metric("Fallidos", stats.get("failed_jobs", 0))

        success_rate = stats.get("success_rate", 0)
        fig = px.bar(
            x=["Procesados", "Fallidos"],
            y=[stats.get("processed_files", 0), stats.get("failed_files", 0)],
            color_discrete_sequence=["#2EAFC4", "#FF6B6B"],
        )
        fig.update_layout(height=240, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Tasa de exito: {success_rate:.2f}%")


__all__ = [
    "FileUploader",
    "FolderSelector",
    "GitHubRepositoryForm",
    "MarkdownEditor",
    "JobMonitor",
    "StatisticsDisplay",
]

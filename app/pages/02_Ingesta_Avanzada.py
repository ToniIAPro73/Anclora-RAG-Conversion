"""Streamlit page exposing the advanced ingestion workflows."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from app.ingestion import AdvancedIngestionSystem, IngestionJob, IngestionStatus, RepositoryOptions
from app.components.ingestion_ui_components import (
    FileUploader,
    FolderSelector,
    GitHubRepositoryForm,
    JobMonitor,
    MarkdownEditor,
    StatisticsDisplay,
)

st.set_page_config(page_title="Ingesta Avanzada", page_icon=":inbox_tray:", layout="wide")


@st.cache_resource
def _get_system() -> AdvancedIngestionSystem:
    return AdvancedIngestionSystem()


ingestion_system = _get_system()

if "user_id" not in st.session_state:
    st.session_state["user_id"] = "default_user"

st.title("Sistema de Ingesta Avanzada")
st.caption("Gestiona archivos individuales, carpetas y fuentes markdown desde un solo lugar.")

tab_archivos, tab_carpetas, tab_markdown, tab_github, tab_jobs, tab_stats = st.tabs(
    [
        "Archivos",
        "Carpetas",
        "Fuentes Markdown",
        "Repositorios GitHub",
        "Trabajos",
        "Estadisticas",
    ]
)


def _register_job(job: IngestionJob) -> None:
    jobs: Dict[str, IngestionJob] = st.session_state.setdefault("advanced_ingestion_jobs", {})
    jobs[job.job_id] = job


def _job_to_dict(job: IngestionJob) -> Dict[str, Any]:
    data = asdict(job)
    data["status"] = job.status
    return data


def _show_job_feedback(job: IngestionJob) -> None:
    if job.status == IngestionStatus.COMPLETED:
        st.success(f"Trabajo {job.job_id} completado: {job.processed_files}/{job.total_files} archivos procesados")
    elif job.status == IngestionStatus.PARTIALLY_COMPLETED:
        st.warning(
            f"Trabajo {job.job_id} parcialmente completado: {job.processed_files}/{job.total_files} archivos y "
            f"{job.failed_files} errores"
        )
    else:
        st.error(
            f"Trabajo {job.job_id} fallido. Revisar detalles en la seccion de trabajos."
        )


with tab_archivos:
    uploader = FileUploader(label="Selecciona archivos para importar")
    uploaded_files = uploader.render(ingestion_system.supported_formats)
    if uploaded_files:
        info_rows = []
        for file_obj in uploaded_files:
            size = getattr(file_obj, "size", None)
            if size is None and hasattr(file_obj, "getbuffer"):
                size = len(file_obj.getbuffer())
            info_rows.append(
                {
                    "Archivo": getattr(file_obj, "name", "sin_nombre"),
                    "Tamanio (MB)": (size or 0) / (1024 * 1024),
                }
            )
        df_info = pd.DataFrame(info_rows)
        st.dataframe(df_info, use_container_width=True)
        if st.button("Procesar archivos seleccionados"):
            with st.spinner("Procesando archivos..."):
                job = asyncio.run(
                    ingestion_system.ingest_files(
                        uploaded_files,
                        user_id=st.session_state["user_id"],
                        metadata={"origin": "advanced_ingestion_ui"},
                    )
                )
                _register_job(job)
                _show_job_feedback(job)
                if job.errors:
                    st.json(job.errors)

with tab_carpetas:
    controls = FolderSelector().render()
    folder_path = controls["folder_path"]
    if controls["analyze"] and folder_path:
        with st.spinner("Analizando carpeta..."):
            report = asyncio.run(
                ingestion_system.folder_processor.create_folder_report(
                    folder_path,
                    ingestion_system.supported_formats,
                )
            )
            st.session_state["folder_report"] = report
            st.success(f"Se detectaron {report['discovered_files']['total']} archivos candidatos")
    if folder_path and st.button("Procesar carpeta"):
        with st.spinner("Procesando carpeta..."):
            job = asyncio.run(
                ingestion_system.ingest_folder(
                    folder_path,
                    user_id=st.session_state["user_id"],
                    recursive=controls["recursive"],
                    metadata={"origin": "advanced_ingestion_ui"},
                )
            )
            _register_job(job)
            _show_job_feedback(job)
    if "folder_report" in st.session_state:
        report = st.session_state["folder_report"]
        st.subheader("Resumen de carpeta")
        details = report["discovered_files"]["by_category"]
        df_report = pd.DataFrame(list(details.items()), columns=["Categoria", "Cantidad"])
        st.dataframe(df_report, use_container_width=True)
        st.caption("Recomendaciones")
        for item in report.get("recommendations", []):
            st.write(f"- {item}")

with tab_markdown:
    parser = ingestion_system.markdown_parser
    if st.button("Generar plantilla en espanol"):
        st.session_state["markdown_template"] = asyncio.run(parser.generate_template("es"))
    template = st.session_state.get("markdown_template", "")
    editor_response = MarkdownEditor().render(default_text=template)
    content = editor_response["content"]
    if editor_response["preview"] and content:
        validation = asyncio.run(parser.validate_source_format(content))
        if validation["valid"]:
            st.success(f"Formato valido. Fuentes detectadas: {validation['source_count']}")
        else:
            st.error("Formato invalido")
            st.json(validation)
    if editor_response["ingest"] and content:
        with st.spinner("Procesando fuentes markdown..."):
            job = asyncio.run(
                ingestion_system.ingest_markdown_sources(
                    content,
                    user_id=st.session_state["user_id"],
                    source_name="markdown_ui",
                    metadata={"origin": "advanced_ingestion_ui"},
                )
            )
            _register_job(job)
            _show_job_feedback(job)


with tab_github:
    st.header("Repositorios de GitHub")
    form_response = GitHubRepositoryForm().render()
    repo_url = form_response["repo_url"]
    branch = form_response["branch"] or ""
    options = form_response["options"]
    analysis_key = "github_analysis"

    if form_response["analyze"]:
        if not repo_url:
            st.warning("Proporciona la URL del repositorio publico que deseas analizar.")
        else:
            previous = st.session_state.get(analysis_key)
            if previous and previous.get("temp_path"):
                asyncio.run(ingestion_system.github_processor.cleanup_repository(previous["temp_path"]))
            with st.spinner("Analizando repositorio..."):
                repo_options = RepositoryOptions(**options)
                analysis = asyncio.run(
                    ingestion_system.github_processor.analyze_repository(repo_url, branch or None, repo_options)
                )
            if analysis.get("success"):
                analysis["options"] = options
                st.session_state[analysis_key] = analysis
                st.success(
                    f"Analisis completado: {analysis['total_files']} archivos candidatos ("                    f"{analysis['total_size_mb']} MB)"
                )
            else:
                st.error(analysis.get("error", "No fue posible analizar el repositorio."))
                st.session_state.pop(analysis_key, None)

    if form_response["ingest"]:
        if not repo_url:
            st.warning("Debes indicar la URL del repositorio para procesarlo.")
        else:
            stored_analysis = st.session_state.get(analysis_key)
            if stored_analysis and stored_analysis.get("repository") != repo_url:
                stored_analysis = None
            with st.spinner("Procesando repositorio..."):
                job = asyncio.run(
                    ingestion_system.ingest_github_repository(
                        repo_url,
                        user_id=st.session_state["user_id"],
                        branch=branch or None,
                        options=options,
                        metadata={"origin": "github_repository"},
                        analysis=stored_analysis,
                    )
                )
            _register_job(job)
            _show_job_feedback(job)
            if job.errors:
                st.json(job.errors)
            st.session_state.pop(analysis_key, None)

    analysis_data = st.session_state.get(analysis_key)
    if analysis_data and analysis_data.get("success"):
        st.subheader("Resumen del analisis")
        col1, col2, col3 = st.columns(3)
        col1.metric("Archivos", analysis_data.get("total_files", 0))
        col2.metric("Tamano (MB)", analysis_data.get("total_size_mb", 0))
        col3.metric("Branch", analysis_data.get("branch", "-"))
        by_ext = analysis_data.get("by_extension") or {}
        if by_ext:
            df_ext = pd.DataFrame(
                sorted(((ext, count) for ext, count in by_ext.items()), key=lambda item: item[1], reverse=True),
                columns=["Extension", "Cantidad"],
            )
            st.dataframe(df_ext, use_container_width=True)

with tab_jobs:
    stored_jobs = list(st.session_state.get("advanced_ingestion_jobs", {}).values())
    jobs_payload: List[Dict[str, Any]] = [_job_to_dict(job) for job in stored_jobs]
    JobMonitor.render(jobs_payload)

with tab_stats:
    stats = ingestion_system.get_statistics()
    StatisticsDisplay.render(stats)

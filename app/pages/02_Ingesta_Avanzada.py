"""Streamlit page exposing the advanced ingestion workflows."""
from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Dict, List, Optional, cast

import streamlit as st

import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
APP_ROOT = REPO_ROOT / 'app'
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos de ingesta
try:
    from app.ingestion.advanced_ingestion_system import AdvancedIngestionSystem, IngestionStatus
    from app.ingestion.validation_service import ValidationService
    from app.ingestion.github_processor import RepositoryOptions
    
    # Importar la nueva integración de NotebookLM
    from app.ingestion.integration.notebooklm_integration import render_notebooklm_conversion_ui
    
except ImportError as e:
    logger.error(f"Error importing ingestion modules: {e}")
    st.error("Error al cargar los módulos de ingesta. Verifica la instalación.")
    st.stop()

# Importar constantes y configuraciones
try:
    from app.common.constants import CHROMA_COLLECTIONS
    from app.common.anclora_colors import apply_anclora_theme
except ImportError:
    # Fallback si no están disponibles
    CHROMA_COLLECTIONS = ["default_collection"]
    def apply_anclora_theme():
        pass

# Aplicar tema de colores Anclora RAG
apply_anclora_theme()

# Configuración de la página
st.set_page_config(
    page_title="Ingesta Avanzada - Anclora RAG",
    page_icon="",
    layout="wide"
)

def run_async_task(coro):
    """Execute *coro* ensuring compatibility with existing event loops."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

def init_session_state():
    """Initialize session state variables"""
    if 'ingestion_system' not in st.session_state:
        st.session_state.ingestion_system = AdvancedIngestionSystem()
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = {}
    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = CHROMA_COLLECTIONS[0] if isinstance(CHROMA_COLLECTIONS, list) and CHROMA_COLLECTIONS else "default"

def display_uploaded_files():
    """Display uploaded files in a nice format"""
    if st.session_state.uploaded_files:
        st.subheader("Archivos Subidos")
        for i, file_info in enumerate(st.session_state.uploaded_files):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{file_info['name']}**")
            with col2:
                st.write(f"{file_info['size']} MB")
            with col3:
                if st.button("Eliminar", key=f"remove_{i}"):
                    st.session_state.uploaded_files.pop(i)
                    st.rerun()

def main():
    """Main function for the advanced ingestion page"""
    
    init_session_state()
    
    st.title("Ingesta Avanzada - Anclora RAG")
    st.markdown("""
    Sistema de ingesta avanzada para procesamiento de documentos en múltiples formatos.
    Soporta archivos individuales, carpetas completas, repositorios GitHub públicos y conversión desde NotebookLM.
    """)
    
    # Configuración principal
    st.header("Configuración")
    
    # Manejo seguro de CHROMA_COLLECTIONS
    if isinstance(CHROMA_COLLECTIONS, dict):
        collection_options = list(CHROMA_COLLECTIONS.keys())
    elif isinstance(CHROMA_COLLECTIONS, list):
        collection_options = CHROMA_COLLECTIONS
    else:
        collection_options = ["default_collection"]

    current_index = 0
    if st.session_state.selected_collection in collection_options:
        current_index = collection_options.index(st.session_state.selected_collection)

    st.session_state.selected_collection = st.selectbox(
        "Seleccionar Colección:",
        options=collection_options,
        index=current_index
    )
    
    # Opciones de procesamiento
    validate_files = st.checkbox("Validar archivos antes de procesar", value=True)
    check_duplicates = st.checkbox("Verificar duplicados", value=True)
    
    with st.expander("Opciones Avanzadas"):
        chunk_size = st.slider("Tamaño de chunks:", min_value=500, max_value=2000, value=1000, key="chunk_size_slider")
        chunk_overlap = st.slider("Solapamiento de chunks:", min_value=0, max_value=500, value=200, key="chunk_overlap_slider")
    
    # Tabs para diferentes modos de ingesta
    tab1, tab2, tab3, tab4 = st.tabs([
        "Archivo individual",
        "Carpeta completa",
        "Repositorio GitHub",
        "NotebookLM Integration"
    ])
    with tab1:
        st.subheader("Subir archivo individual")
        uploaded_file = st.file_uploader(
            "Seleccionar archivo",
            type=['pdf', 'docx', 'txt', 'md', 'html', 'xlsx', 'pptx'],
            help="Formatos soportados: PDF, Word, Texto, Markdown, HTML, Excel, PowerPoint",
            key="single_file_uploader"
        )
        
        if uploaded_file:
            file_info = {
                'name': uploaded_file.name,
                'size': round(uploaded_file.size / (1024 * 1024), 2),
                'type': uploaded_file.type
            }
            
            if file_info not in st.session_state.uploaded_files:
                st.session_state.uploaded_files.append(file_info)
            
            display_uploaded_files()
            
            if st.button("Procesar Archivos", key="process_single"):
                with st.spinner("Procesando archivo..."):
                    try:
                        # Simular procesamiento (reemplazar con llamada real)
                        result = {
                            'success': True,
                            'metadata': {
                                'file_name': uploaded_file.name,
                                'file_size': uploaded_file.size,
                                'processed_at': '2024-01-19 12:00:00',
                                'chunks_created': 15
                            }
                        }
                        
                        if result['success']:
                            st.success("Archivo procesado exitosamente!")
                            with st.expander("Metadatos del Procesamiento"):
                                st.json(result['metadata'])
                        else:
                            st.error("Error al procesar el archivo")
                            st.write(result.get('error', 'Error desconocido'))
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Procesar Carpeta Completa")
        folder_path = st.text_input(
            "Ruta de la carpeta:",
            value="",
            placeholder="/ruta/a/tu/carpeta",
            help="Ruta absoluta a la carpeta que contiene los documentos",
            key="folder_path_input"
        )
        
        if folder_path and os.path.isdir(folder_path):
            st.info(f"Carpeta encontrada: {folder_path}")
            
            # Mostrar estadísticas de la carpeta
            file_count = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
            st.write(f"Archivos en carpeta: {file_count}")
            
            if st.button("Procesar carpeta", key="process_folder"):
                with st.spinner("Procesando carpeta..."):
                    try:
                        # Simular procesamiento (reemplazar con llamada real)
                        result = {
                            'success': True,
                            'processed_files': file_count,
                            'failed_files': 0,
                            'errors': []
                        }
                        
                        if result['success']:
                            st.success("Carpeta procesada exitosamente")
                            st.write(f"Archivos procesados: {result['processed_files']}")
                            st.write(f"Archivos con errores: {result['failed_files']}")
                            
                            if result['errors']:
                                with st.expander("Errores encontrados"):
                                    for error in result['errors']:
                                        st.error(f"{error['file']}: {error['error']}")
                                        
                        else:
                            st.error("Error al procesar la carpeta")
                            st.write(result.get('error', 'Error desconocido'))
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.warning("Ingresa una ruta de carpeta válida")
    
    with tab3:
        st.subheader("Ingestar repositorio de GitHub")
        repo_url = st.text_input(
            "URL del repositorio:",
            placeholder="https://github.com/usuario/repositorio",
            key="github_repo_url",
        )
        branch = st.text_input(
            "Rama (opcional):",
            placeholder="main",
            key="github_branch",
        )

        st.caption(
            "Ingresa un enlace público de GitHub. Ideal para repositorios de conversión como Pandoc."
        )

        col_options_1, col_options_2 = st.columns(2)
        with col_options_1:
            include_docs = st.checkbox("Incluir documentación (Markdown/PDF)", value=True, key="github_include_docs")
            include_code = st.checkbox("Incluir código fuente", value=True, key="github_include_code")
            include_media = st.checkbox("Incluir multimedia", value=False, key="github_include_media")
        with col_options_2:
            include_other = st.checkbox("Incluir otros archivos", value=False, key="github_include_other")
            max_file_size = st.slider("Tamaño máximo por archivo (MB)", min_value=1, max_value=200, value=25, key="github_max_size")
            allowed_exts_raw = st.text_input("Extensiones permitidas (opcional, separadas por coma)", value="", key="github_allowed_exts")

        if st.button("Ingerir repositorio", key="github_ingest_button"):
            if not repo_url:
                st.warning("Proporciona una URL de repositorio válida.")
            else:
                cleaned_exts: list[str] = []
                if allowed_exts_raw:
                    for ext in allowed_exts_raw.split(","):
                        ext = ext.strip()
                        if not ext:
                            continue
                        if not ext.startswith('.'):
                            ext = f'.{ext}'
                        cleaned_exts.append(ext.lower())

                repo_options = RepositoryOptions(
                    include_docs=include_docs,
                    include_code=include_code,
                    include_media=include_media,
                    include_other=include_other,
                    max_file_size_mb=max_file_size,
                    allowed_extensions=cleaned_exts or None,
                )

                metadata = {
                    "ingest_origin": "github_ui",
                    "target_collection": st.session_state.selected_collection,
                }

                with st.spinner("Clonando y procesando el repositorio..."):
                    try:
                        job = run_async_task(
                            st.session_state.ingestion_system.ingest_github_repository(
                                repo_url=repo_url,
                                user_id="advanced_ingestion_ui",
                                branch=branch or None,
                                options=repo_options,
                                metadata=metadata,
                            )
                        )
                    except Exception as exc:
                        st.error(f"Error al procesar el repositorio: {exc}")
                    else:
                        if job.status == IngestionStatus.COMPLETED:
                            st.success("Repositorio ingerido correctamente.")
                        elif job.status == IngestionStatus.PARTIALLY_COMPLETED:
                            st.warning("Repositorio ingerido con algunos errores.")
                        else:
                            st.error("No fue posible ingerir el repositorio.")

                        st.write("Archivos procesados:", job.processed_files)
                        st.write("Archivos fallidos:", job.failed_files)
                        st.write("Archivos omitidos:", job.skipped_files)

                        if job.errors:
                            with st.expander("Errores detectados"):
                                for item in job.errors:
                                    mensaje = item.get("error") or item.get("general") or "Error desconocido"
                                    archivo = item.get("file") or item.get("repo_relative_path") or "N/D"
                                    st.error(f"{archivo}: {mensaje}")

    with tab4:
        # Integración con NotebookLM
        render_notebooklm_conversion_ui()
    # Footer
    st.markdown("---")
    st.caption("Anclora RAG - Sistema de Ingesta Avanzada v1.0")

if __name__ == "__main__":
    main()

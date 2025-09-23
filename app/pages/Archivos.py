import streamlit as st
import os
import pandas as pd
from pathlib import Path

# Set page config
st.set_page_config(layout='wide', page_title='Archivos - Anclora AI RAG', page_icon='📁')

# Simple CSS to hide Streamlit elements
hide_st_style = """
    <style>
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize language in session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# Add the parent directory to Python path for imports
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Try to import ingest functions
INGEST_AVAILABLE = False
ingest_file = None
validate_uploaded_file = None
get_unique_sources_df = None
delete_file_from_vectordb = None
SUPPORTED_EXTENSIONS = []
CHROMA_SETTINGS = None

try:
    from common.ingest_file import ingest_file, validate_uploaded_file, get_unique_sources_df, delete_file_from_vectordb, SUPPORTED_EXTENSIONS
    from common.constants import CHROMA_SETTINGS
    INGEST_AVAILABLE = True
    st.success("✅ Módulos de ingesta cargados correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar módulos de ingesta: {e}")
    st.info("🔧 Verificando configuración del sistema...")

# Sidebar for language selection
with st.sidebar:
    st.header("Idioma")
    language_options = {
        'es': 'Español',
        'en': 'English'
    }

    selected_language = st.selectbox(
        "Selecciona idioma:",
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=0 if st.session_state.language == 'es' else 1,
        key="language_selector"
    )

    # Update session state if language changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()

# Main content
if st.session_state.language == 'es':
    st.title("📁 Gestión de Archivos")
    st.caption("Sube y gestiona documentos para el sistema RAG")
    upload_label = "Subir archivo"
    add_button_text = "Añadir a la base de conocimiento"
    files_table_title = "Archivos en la base de datos"
    delete_button_text = "Eliminar archivo"
    processing_message = "Procesando archivo..."
    success_message = "Archivo agregado exitosamente"
    error_message = "Error al procesar archivo"
    no_files_message = "No hay archivos en la base de datos actualmente."
    upload_first_message = "Por favor, sube un archivo primero."
else:
    st.title("📁 File Management")
    st.caption("Upload and manage documents for the RAG system")
    upload_label = "Upload file"
    add_button_text = "Add to knowledge base"
    files_table_title = "Files in database"
    delete_button_text = "Delete file"
    processing_message = "Processing file..."
    success_message = "File added successfully"
    error_message = "Error processing file"
    no_files_message = "No files in database currently."
    upload_first_message = "Please upload a file first."

# Check if ingest functionality is available
if not INGEST_AVAILABLE:
    if st.session_state.language == 'es':
        st.error("⚠️ Los módulos de ingesta no están disponibles. Verifica la configuración del sistema.")
    else:
        st.error("⚠️ Ingest modules are not available. Please check system configuration.")
    st.stop()

# Show supported file types
if INGEST_AVAILABLE:
    supported_types = [ext.replace('.', '') for ext in SUPPORTED_EXTENSIONS]
    if st.session_state.language == 'es':
        st.info(f"📋 **Tipos de archivo soportados:** {', '.join(supported_types)}")
    else:
        st.info(f"📋 **Supported file types:** {', '.join(supported_types)}")

# File uploader
uploaded_file = st.file_uploader(
    upload_label,
    type=supported_types if INGEST_AVAILABLE else ['pdf', 'txt', 'docx', 'md'],
    accept_multiple_files=False,
    help=f"Límite: 10MB. Tipos soportados: {', '.join(supported_types) if INGEST_AVAILABLE else 'PDF, TXT, DOCX, MD'}"
)

# Process file button
if st.button(add_button_text, type="primary"):
    if uploaded_file:
        if INGEST_AVAILABLE:
            # Validate file first
            is_valid, validation_message = validate_uploaded_file(uploaded_file)

            if is_valid:
                with st.spinner(processing_message):
                    try:
                        # Process the file
                        ingest_file(uploaded_file, uploaded_file.name)
                        st.success(f"✅ {success_message}: {uploaded_file.name}")
                        st.rerun()  # Refresh to show updated file list
                    except Exception as e:
                        st.error(f"❌ {error_message}: {str(e)}")
            else:
                st.error(f"❌ {validation_message}")
        else:
            st.error("❌ Sistema de ingesta no disponible")
    else:
        st.warning(f"⚠️ {upload_first_message}")

# Display current files in database
st.subheader(files_table_title)

if INGEST_AVAILABLE:
    try:
        # Get files from database
        files_df = get_unique_sources_df(CHROMA_SETTINGS)

        if not files_df.empty:
            # Display files table
            display_df = files_df[['uploaded_file_name', 'domain', 'collection']].copy()
            display_df.columns = ['Archivo', 'Dominio', 'Colección'] if st.session_state.language == 'es' else ['File', 'Domain', 'Collection']

            st.dataframe(display_df, use_container_width=True)

            # Delete file functionality
            st.subheader("🗑️ Eliminar archivo" if st.session_state.language == 'es' else "🗑️ Delete file")

            file_to_delete = st.selectbox(
                "Seleccionar archivo para eliminar:" if st.session_state.language == 'es' else "Select file to delete:",
                options=files_df['uploaded_file_name'].tolist(),
                key="file_to_delete"
            )

            if st.button(delete_button_text, type="secondary"):
                if file_to_delete:
                    with st.spinner("Eliminando archivo..." if st.session_state.language == 'es' else "Deleting file..."):
                        try:
                            success = delete_file_from_vectordb(file_to_delete)
                            if success:
                                st.success(f"✅ Archivo eliminado: {file_to_delete}")
                                st.rerun()
                            else:
                                st.warning(f"⚠️ No se pudo eliminar el archivo: {file_to_delete}")
                        except Exception as e:
                            st.error(f"❌ Error al eliminar archivo: {str(e)}")
        else:
            st.info(f"📂 {no_files_message}")

    except Exception as e:
        st.error(f"❌ Error al obtener archivos: {str(e)}")
else:
    st.info(f"📂 {no_files_message}")

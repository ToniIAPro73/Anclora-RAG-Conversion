import streamlit as st
import os
import pandas as pd
from pathlib import Path
import logging
import html
from typing import Any, cast

# Set page config
st.set_page_config(layout='wide', page_title='Archivos - Anclora AI RAG', page_icon='📁')

# Add the parent directory to Python path for imports
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert
from common.constants import CHROMA_COLLECTIONS

# Aplicar tema de colores Anclora RAG
apply_anclora_theme()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

# Streamlit compatibility helpers
_st = cast(Any, st)

def markdown_html(markdown_text: str) -> None:
    """Render HTML content safely across Streamlit versions."""
    markdown_fn = getattr(_st, 'markdown', None)
    if callable(markdown_fn):
        try:
            markdown_fn(markdown_text, unsafe_allow_html=True)
        except TypeError:
            markdown_fn(markdown_text)
    else:
        st.write(markdown_text)

def show_caption(message: str) -> None:
    caption_fn = getattr(_st, 'caption', None)
    if callable(caption_fn):
        caption_fn(message)
    else:
        markdown_html(f"<p class='st-caption'>{html.escape(message)}</p>")

def stop_app() -> None:
    stop_fn = getattr(_st, 'stop', None)
    if callable(stop_fn):
        stop_fn()
    else:
        raise RuntimeError('Streamlit.stop is not available in this version')

def show_checkbox(label: str, **kwargs: Any) -> bool:
    checkbox_fn = getattr(_st, 'checkbox', None)
    if callable(checkbox_fn):
        return bool(checkbox_fn(label, **kwargs))
    toggle_fn = getattr(_st, 'toggle', None)
    if callable(toggle_fn):
        return bool(toggle_fn(label, **kwargs))
    raise RuntimeError('Streamlit.checkbox is not available in this version')

def show_code(code_block: str, language: str = 'text') -> None:
    code_fn = getattr(_st, 'code', None)
    if callable(code_fn):
        code_fn(code_block, language=language)
    else:
        markdown_html(f"<pre><code>{html.escape(code_block)}</code></pre>")

def show_metric(label: str, value: Any) -> None:
    metric_fn = getattr(_st, 'metric', None)
    if callable(metric_fn):
        metric_fn(label=label, value=value)
    else:
        st.write(f"{label}: {value}")

def get_text_input(label: str, **kwargs: Any) -> str:
    text_input_fn = getattr(_st, 'text_input', None)
    if callable(text_input_fn):
        return str(text_input_fn(label, **kwargs))
    text_area_fn = getattr(_st, 'text_area', None)
    if callable(text_area_fn):
        return str(text_area_fn(label, **kwargs))
    raise RuntimeError('Streamlit.text_input is not available in this version')

# CSS personalizado con colores Anclora RAG
custom_style = f"""
    <style>
        /* ============================================
           GLOBAL STREAMLIT ELEMENT HIDING
           ============================================ */
        #MainMenu {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        footer {{visibility: hidden;}}
        #stDecoration {{display:none;}}
        .stApp > div[data-testid="stToolbar"] {{display: none;}}

        /* ============================================
           SIDEBAR STYLING
           ============================================ */
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] .stMarkdown h3,
        section[data-testid="stSidebar"] h3,
        .sidebar h3 {{
            color: white !important;
        }}

        div[data-testid="stSidebar"] .stSelectbox label,
        div[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] label {{
            color: white !important;
            font-weight: 600 !important;
        }}

        .sidebar .stSelectbox > div > div {{
            background-color: rgba(255,255,255,0.1) !important;
            border: 2px solid #2EAFC4 !important;
            border-radius: 8px !important;
            color: white !important;
        }}

        /* ============================================
           FILE UPLOADER STYLING
           ============================================ */
        .stFileUploader label {{
            color: white !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }}

        .stFileUploader > div > div {{
            background-color: {ANCLORA_RAG_COLORS['neutral_medium']} !important;
            border: 2px solid white !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
        }}

        .stFileUploader button {{
            background-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border-radius: 8px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
        }}

        .stFileUploader button:hover {{
            background-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
            border-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
        }}

        /* ============================================
           BUTTON STYLING
           ============================================ */
        .stButton > button {{
            background: linear-gradient(135deg, {ANCLORA_RAG_COLORS['success_deep']} 0%, {ANCLORA_RAG_COLORS['success_medium']} 100%) !important;
            border: 2px solid {ANCLORA_RAG_COLORS['success_deep']} !important;
            border-radius: 12px !important;
            color: #1a4d47 !important;
            font-weight: 700 !important;
            padding: 0.6rem 1.5rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}

        .stButton > button:hover {{
            background: {ANCLORA_RAG_COLORS['success_deep']} !important;
            color: #0f3027 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important;
        }}

        /* ============================================
           DATAFRAME STYLING
           ============================================ */
        .stDataFrame {{
            border: 2px solid {ANCLORA_RAG_COLORS['primary_light']} !important;
            border-radius: 12px !important;
        }}

        /* ============================================
           FILES TITLE STYLING
           ============================================ */
        .files-title {{
            color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            margin-bottom: 1rem !important;
        }}
    </style>
    <script>
        // Suppress 404 console errors
        const originalFetch = window.fetch;
        window.fetch = function(...args) {{
            return originalFetch.apply(this, args).catch(err => {{
                if (!err.message.includes('404')) console.error(err);
                return Promise.reject(err);
            }});
        }};
    </script>
"""
markdown_html(custom_style)

# Initialize language in session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

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
    markdown_html("<h3>🌐 Idioma</h3>")

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
    show_caption("Sube y gestiona documentos para el sistema RAG")
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
    show_caption("Upload and manage documents for the RAG system")
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
    stop_app()

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


if st.button(add_button_text):
    if uploaded_file:
        logger.info(f"File upload initiated: {uploaded_file.name}")
        if INGEST_AVAILABLE:
            # Validate file first
            is_valid, validation_message = validate_uploaded_file(uploaded_file)
            logger.info(f"File validation result for {uploaded_file.name}: {is_valid}")

            if is_valid:
                # Additional security checks
                file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                max_size_mb = 10  # 10MB limit

                if file_size_mb > max_size_mb:
                    st.error(f"❌ El archivo es demasiado grande: {file_size_mb:.1f}MB. Límite máximo: {max_size_mb}MB" if st.session_state.language == 'es' else f"❌ File is too large: {file_size_mb:.1f}MB. Maximum limit: {max_size_mb}MB")
                else:
                    # Check for suspicious file patterns
                    filename = uploaded_file.name.lower()
                    suspicious_patterns = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.jar', '.zip', '.rar', '.7z']
                    is_suspicious = any(pattern in filename for pattern in suspicious_patterns)

                    if is_suspicious:
                        st.warning(f"⚠️ El archivo '{uploaded_file.name}' tiene una extensión potencialmente peligrosa. ¿Estás seguro de que quieres procesarlo?" if st.session_state.language == 'es' else f"⚠️ The file '{uploaded_file.name}' has a potentially dangerous extension. Are you sure you want to process it?")

                        if st.button("🔓 Procesar archivo de todos modos" if st.session_state.language == 'es' else "🔓 Process file anyway", type="secondary"):
                            process_file = True
                        else:
                            st.info("✅ Procesamiento cancelado por seguridad" if st.session_state.language == 'es' else "✅ Processing cancelled for security")
                            process_file = False
                    else:
                        process_file = True

                    if process_file:
                        with st.spinner(processing_message):
                            try:
                                st.info(f"🔄 Iniciando procesamiento de: {uploaded_file.name} ({file_size_mb:.1f}MB)" if st.session_state.language == 'es' else f"🔄 Starting processing of: {uploaded_file.name} ({file_size_mb:.1f}MB)")

                                # Process the file
                                result = ingest_file(uploaded_file, uploaded_file.name)

                                st.info(f"📊 Resultado: {result}")

                                if result and result.get("success"):
                                    # Get domain information from the result if available
                                    domain_info = ""
                                    if result.get("domain"):
                                        domain_info = f" (Dominio: {result.get('domain')})"
                                    elif result.get("collection"):
                                        # Try to get domain from collection name
                                        collection_config = CHROMA_COLLECTIONS.get(result.get("collection"))
                                        if collection_config:
                                            domain_info = f" (Dominio: {collection_config.domain})"

                                    logger.info(f"File processed successfully: {uploaded_file.name}{domain_info}")
                                    st.success(f"✅ {success_message}: {uploaded_file.name}{domain_info}")
                                    # Trigger refresh by updating a session state variable
                                    if 'files_refresh_trigger' not in st.session_state:
                                        st.session_state.files_refresh_trigger = 0
                                    st.session_state.files_refresh_trigger += 1
                                else:
                                    error_msg = result.get("error", "Error desconocido") if result else "Sin resultado"
                                    logger.error(f"File processing failed: {uploaded_file.name} - {error_msg}")
                                    st.error(f"❌ {error_message}: {error_msg}")

                            except Exception as e:
                                error_details = str(e)
                                if "Connection" in error_details or "timeout" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de conexión. Verifica la configuración de la base de datos." if st.session_state.language == 'es' else f"❌ {error_message}: Connection error. Please check database configuration.")
                                elif "Permission" in error_details or "access" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de permisos. Verifica los permisos de escritura en la base de datos." if st.session_state.language == 'es' else f"❌ {error_message}: Permission error. Please check database write permissions.")
                                elif "Memory" in error_details or "out of memory" in error_details.lower():
                                    st.error(f"❌ {error_message}: Error de memoria. El archivo podría ser demasiado grande." if st.session_state.language == 'es' else f"❌ {error_message}: Memory error. The file might be too large.")
                                else:
                                    st.error(f"❌ {error_message}: {error_details}" if st.session_state.language == 'es' else f"❌ {error_message}: {error_details}")
                                # Only show stack trace in development/debug mode
                                if show_checkbox("Mostrar detalles técnicos" if st.session_state.language == 'es' else "Show technical details", key="show_error_details"):
                                    show_code(f"Error: {type(e).__name__}: {error_details}", language="text")
            else:
                st.error(f"❌ {validation_message}")
        else:
            st.error("❌ Sistema de ingesta no disponible")
    else:
        st.warning(f"⚠️ {upload_first_message}")

# Display current files in database
markdown_html(f'<h3 class="files-title">{files_table_title}</h3>')

if INGEST_AVAILABLE:
    try:
        # Get files from database
        files_df = get_unique_sources_df(CHROMA_SETTINGS)

        if not files_df.empty:
            # Filters section
            st.subheader("🔍 Filtros de búsqueda" if st.session_state.language == 'es' else "🔍 Search filters")

            col1, col2 = st.columns(2)

            with col1:
                # Domain filter
                available_domains = sorted(files_df['domain'].unique().tolist())
                domain_options = ['Todos los dominios'] + available_domains if st.session_state.language == 'es' else ['All domains'] + available_domains

                selected_domain = st.selectbox(
                    "Dominio:" if st.session_state.language == 'es' else "Domain:",
                    options=domain_options,
                    index=0,
                    key="domain_filter"
                )

            with col2:
                # Collection filter
                available_collections = sorted(files_df['collection'].unique().tolist())
                collection_options = ['Todas las colecciones'] + available_collections if st.session_state.language == 'es' else ['All collections'] + available_collections

                selected_collection = st.selectbox(
                    "Colección:" if st.session_state.language == 'es' else "Collection:",
                    options=collection_options,
                    index=0,
                    key="collection_filter"
                )

            # Apply filters using a more maintainable approach
            def apply_filter(df, filter_value, filter_column, all_values_text):
                """Apply a single filter to the dataframe"""
                if filter_value != all_values_text:
                    return df[df[filter_column] == filter_value]
                return df

            # Apply filters
            all_domains_text = 'Todos los dominios' if st.session_state.language == 'es' else 'All domains'
            all_collections_text = 'Todas las colecciones' if st.session_state.language == 'es' else 'All collections'

            filtered_df = files_df.copy()
            filtered_df = apply_filter(filtered_df, selected_domain, 'domain', all_domains_text)
            filtered_df = apply_filter(filtered_df, selected_collection, 'collection', all_collections_text)

            # Show filter status
            active_filters = []
            if selected_domain != all_domains_text:
                active_filters.append(f"dominio '{selected_domain}'")
            if selected_collection != all_collections_text:
                active_filters.append(f"colección '{selected_collection}'")

            if active_filters:
                filter_text = " y ".join(active_filters) if st.session_state.language == 'es' else " and ".join(active_filters)
                st.info(f"📊 Mostrando {len(filtered_df)} archivos de {filter_text}" if st.session_state.language == 'es' else f"📊 Showing {len(filtered_df)} files from {filter_text}")
            else:
                st.info(f"📊 Mostrando todos los {len(filtered_df)} archivos" if st.session_state.language == 'es' else f"📊 Showing all {len(filtered_df)} files")

            # Display statistics
            if (selected_domain == ('Todos los dominios' if st.session_state.language == 'es' else 'All domains') and
                selected_collection == ('Todas las colecciones' if st.session_state.language == 'es' else 'All collections')):

                st.subheader("📈 Estadísticas por dominio y colección" if st.session_state.language == 'es' else "📈 Domain and collection statistics")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Por Dominio:**" if st.session_state.language == 'es' else "**By Domain:**")
                    # Create domain statistics dataframe
                    domain_stats = files_df.groupby('domain').size().reset_index(name='count')
                    domain_stats.columns = ['Dominio', 'Archivos'] if st.session_state.language == 'es' else ['Domain', 'Files']
                    domain_stats = domain_stats.sort_values('Archivos', ascending=False)

                    # Display domain statistics
                    for _, row in domain_stats.iterrows():
                        show_metric(
                            label=row['Dominio'] if st.session_state.language == 'es' else row['Domain'],
                            value=row['Archivos'] if st.session_state.language == 'es' else row['Files']
                        )

                with col2:
                    st.markdown("**Por Colección:**" if st.session_state.language == 'es' else "**By Collection:**")
                    # Create collection statistics dataframe
                    collection_stats = files_df.groupby('collection').size().reset_index(name='count')
                    collection_stats.columns = ['Colección', 'Archivos'] if st.session_state.language == 'es' else ['Collection', 'Files']
                    collection_stats = collection_stats.sort_values('Archivos', ascending=False)

                    # Display collection statistics
                    for _, row in collection_stats.iterrows():
                        show_metric(
                            label=row['Colección'] if st.session_state.language == 'es' else row['Collection'],
                            value=row['Archivos'] if st.session_state.language == 'es' else row['Files']
                        )

            # Search within filtered results
            search_query = get_text_input(
                "🔍 Buscar archivos:" if st.session_state.language == 'es' else "🔍 Search files:",
                placeholder="Escribe para buscar..." if st.session_state.language == 'es' else "Type to search...",
                key="file_search",
                help="Busca por nombre de archivo, dominio o colección" if st.session_state.language == 'es' else "Search by filename, domain, or collection"
            )

            # Apply search filter with improved logic
            if search_query and search_query.strip():
                search_query = search_query.strip()
                # Use regex for more flexible matching
                import re
                search_pattern = re.compile(re.escape(search_query), re.IGNORECASE)

                search_df = filtered_df[
                    filtered_df['uploaded_file_name'].astype(str).str.contains(search_pattern, na=False, regex=True) |
                    filtered_df['domain'].astype(str).str.contains(search_pattern, na=False, regex=True) |
                    filtered_df['collection'].astype(str).str.contains(search_pattern, na=False, regex=True)
                ].copy()

                if len(search_df) == 0:
                    st.warning(f"⚠️ No se encontraron archivos que coincidan con '{search_query}'" if st.session_state.language == 'es' else f"⚠️ No files found matching '{search_query}'")
                else:
                    st.info(f"🔍 Encontrados {len(search_df)} archivos que coinciden con '{search_query}'" if st.session_state.language == 'es' else f"🔍 Found {len(search_df)} files matching '{search_query}'")
            else:
                search_df = filtered_df.copy()

            # Display files table with performance optimizations
            display_df = search_df[['uploaded_file_name', 'domain', 'collection']].copy()
            display_df.columns = ['Archivo', 'Dominio', 'Colección'] if st.session_state.language == 'es' else ['File', 'Domain', 'Collection']

            # Add pagination for large datasets
            if len(display_df) > 50:
                st.info(f"📊 Mostrando {len(display_df)} archivos. Considera usar los filtros para reducir el número de resultados." if st.session_state.language == 'es' else f"📊 Showing {len(display_df)} files. Consider using filters to reduce the number of results.")

            # Use pagination for better performance
            page_size = 25
            total_pages = (len(display_df) + page_size - 1) // page_size

            if total_pages > 1:
                page_number = st.selectbox(
                    "Página:" if st.session_state.language == 'es' else "Page:",
                    options=list(range(1, total_pages + 1)),
                    index=0,
                    key="files_page"
                )

                start_idx = (page_number - 1) * page_size
                end_idx = min(start_idx + page_size, len(display_df))
                display_page_df = display_df.iloc[start_idx:end_idx].copy()

                st.dataframe(display_page_df, use_container_width=True)
                show_caption(f"Mostrando {start_idx + 1}-{end_idx} de {len(display_df)} archivos" if st.session_state.language == 'es' else f"Showing {start_idx + 1}-{end_idx} of {len(display_df)} files")
            else:
                st.dataframe(display_df, use_container_width=True)

            # Delete file functionality
            st.subheader("🗑️ Eliminar archivo" if st.session_state.language == 'es' else "🗑️ Delete file")

            file_to_delete = st.selectbox(
                "Seleccionar archivo para eliminar:" if st.session_state.language == 'es' else "Select file to delete:",
                options=filtered_df['uploaded_file_name'].tolist(),
                key="file_to_delete"
            )

            # Add confirmation dialog for file deletion
            if file_to_delete:
                st.warning(f"⚠️ **Atención:** Se eliminará permanentemente el archivo '{file_to_delete}' de la base de datos." if st.session_state.language == 'es' else f"⚠️ **Warning:** The file '{file_to_delete}' will be permanently deleted from the database.")

                col1, col2 = st.columns(2)
                with col1:
                    confirm_delete = st.button(
                        "✅ Confirmar eliminación" if st.session_state.language == 'es' else "✅ Confirm deletion",
                        type="primary",
                        help="Eliminar permanentemente el archivo" if st.session_state.language == 'es' else "Permanently delete the file"
                    )
                with col2:
                    cancel_delete = st.button(
                        "❌ Cancelar" if st.session_state.language == 'es' else "❌ Cancel",
                        type="secondary",
                        help="Cancelar la eliminación" if st.session_state.language == 'es' else "Cancel deletion"
                    )

                if confirm_delete:
                    with st.spinner("Eliminando archivo..." if st.session_state.language == 'es' else "Deleting file..."):
                        try:
                            success = delete_file_from_vectordb(file_to_delete)
                            if success:
                                st.success(f"✅ Archivo eliminado exitosamente: {file_to_delete}" if st.session_state.language == 'es' else f"✅ File successfully deleted: {file_to_delete}")
                                # Trigger refresh by updating a session state variable
                                if 'files_refresh_trigger' not in st.session_state:
                                    st.session_state.files_refresh_trigger = 0
                                st.session_state.files_refresh_trigger += 1
                            else:
                                st.error(f"❌ No se pudo eliminar el archivo: {file_to_delete}" if st.session_state.language == 'es' else f"❌ Could not delete file: {file_to_delete}")
                        except Exception as e:
                            st.error(f"❌ Error al eliminar archivo: {str(e)}" if st.session_state.language == 'es' else f"❌ Error deleting file: {str(e)}")

                if cancel_delete:
                    st.info("✅ Eliminación cancelada" if st.session_state.language == 'es' else "✅ Deletion cancelled")
        else:
            st.info(f"📂 {no_files_message}")

    except Exception as e:
        st.error(f"❌ Error al obtener archivos: {str(e)}")
        st.info(f"📂 {no_files_message}")
else:
    st.info(f"📂 {no_files_message}")

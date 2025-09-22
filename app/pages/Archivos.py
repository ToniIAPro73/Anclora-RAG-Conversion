# Try to import streamlit, and if it fails, provide a helpful error message
try:
    import streamlit as st
    st.set_page_config(layout='wide', page_title='Archivos - Anclora AI RAG', page_icon='📁')
except ImportError:
    print("Error: streamlit is not installed. Please install it with 'pip install streamlit'")
    import sys
    sys.exit(1)

import os

try:
    from common.config import get_default_language, get_supported_languages
    from common.ingest_file import (
        SUPPORTED_EXTENSIONS,
        delete_file_from_vectordb,
        get_unique_sources_df,
        ingest_file,
    )
    from common.constants import CHROMA_SETTINGS
    from common.streamlit_style import hide_streamlit_style
    from common.translations import get_text
except ImportError:
    print("Error: common modules not found. Make sure the modules exist and are in the Python path.")
    import sys
    sys.exit(1)

hide_streamlit_style()

# Helper to provide readable labels for the language selector
def _format_language_label(language_code: str, active_language: str, default_language: str) -> str:
    label = get_text(f"language_{language_code}", active_language)
    if label == f"language_{language_code}":
        fallback_label = get_text(f"language_{language_code}", default_language)
        if fallback_label == f"language_{language_code}":
            return language_code.upper()
        return fallback_label
    return label


# Initialize language in session state if not already set
default_language = get_default_language()
available_languages = get_supported_languages()

if default_language not in available_languages:
    available_languages.insert(0, default_language)

if not available_languages:
    available_languages = [default_language]

if "language" not in st.session_state:
    st.session_state.language = default_language

# Reset to default if session stored an unsupported language from a previous version
if st.session_state.language not in available_languages:
    st.session_state.language = default_language

# Add language selector to sidebar
with st.sidebar:
    st.title(get_text("app_title", st.session_state.language))
    st.caption(get_text("sidebar_navigation_hint", st.session_state.language))
    selected_language = st.selectbox(
        get_text("language_selector", st.session_state.language),
        options=available_languages,
        format_func=lambda code: _format_language_label(code, st.session_state.language, default_language),
        index=available_languages.index(st.session_state.language),
        help=get_text("language_selector_help", st.session_state.language)
    )
    
    # Update language if changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()
st.title(get_text("files_title", st.session_state.language))
st.caption(get_text("files_intro", st.session_state.language))

# Carpeta donde se guardarán los archivos en el contenedor del ingestor
container_source_directory = 'documents'

# Función para guardar el archivo cargado en la carpeta
def save_uploaded_file(uploaded_file):
    # Verificar si la carpeta existe en el contenedor, si no, crearla
    if not os.path.exists(container_source_directory):
        os.makedirs(container_source_directory)

    with open(os.path.join(container_source_directory, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    return os.path.join(container_source_directory, uploaded_file.name)

# Widget para cargar archivos
allowed_upload_types = [extension.lstrip('.') for extension in SUPPORTED_EXTENSIONS]
uploaded_files = st.file_uploader(
    get_text("upload_file", st.session_state.language),
    type=allowed_upload_types,
    accept_multiple_files=False,
    help=get_text("file_uploader_help", st.session_state.language, extensions=", ".join(allowed_upload_types))
)
st.caption(get_text("file_uploader_caption", st.session_state.language))

# Botón para ejecutar el script de ingestión
if st.button(
    get_text("add_to_knowledge_base", st.session_state.language),
    help=get_text("add_to_knowledge_base_help", st.session_state.language)
):
    if uploaded_files:
        # Validar archivo antes de procesarlo
        from common.ingest_file import validate_uploaded_file

        is_valid, message = validate_uploaded_file(uploaded_files)
        if is_valid:
            file_name = uploaded_files.name
            st.info(get_text("processing_file", st.session_state.language, file_name=file_name))
            ingest_file(uploaded_files, file_name)
        else:
            st.error(get_text("validation_error", st.session_state.language, message=message))
    else:
        st.warning(get_text("upload_warning", st.session_state.language))

st.subheader(get_text("files_in_knowledge_base", st.session_state.language))
st.caption(get_text("files_table_help", st.session_state.language))

files = get_unique_sources_df(CHROMA_SETTINGS)
column_labels = {
    "uploaded_file_name": get_text("files_column_file", st.session_state.language),
    "domain": get_text("files_column_domain", st.session_state.language),
    "collection": get_text("files_column_collection", st.session_state.language),
}
display_order = list(column_labels.values())
files_display = files.rename(columns=column_labels).reindex(columns=display_order)
files_display['Eliminar'] = False

files_df = st.data_editor(
    files_display,
    use_container_width=True,
    help=get_text("files_table_help", st.session_state.language)
)

selected_files = files_df.loc[files_df['Eliminar']]
file_column = column_labels["uploaded_file_name"]

if len(selected_files) == 1:
    st.divider()
    st.subheader(get_text("delete_file", st.session_state.language))
    file_to_delete = selected_files
    filename = file_to_delete.iloc[0][file_column]
    st.write(filename)
    st.dataframe(file_to_delete, use_container_width=True)
    st.caption(get_text("delete_file_help", st.session_state.language))

    col1, col2, col3 = st.columns(3)

    with col2:
        if st.button(
            get_text("delete_from_knowledge_base", st.session_state.language),
            help=get_text("delete_confirmation_help", st.session_state.language)
        ):
            try:
                delete_file_from_vectordb(filename)
                st.success(get_text("file_deleted", st.session_state.language))
                st.rerun()
            except Exception as e:
                st.error(get_text("delete_error", st.session_state.language, error=str(e)))

elif len(selected_files) > 1:
    st.warning(get_text("one_file_at_a_time", st.session_state.language))
                




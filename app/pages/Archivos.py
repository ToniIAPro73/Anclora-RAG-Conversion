# Try to import streamlit, and if it fails, provide a helpful error message
try:
    import streamlit as st
    st.set_page_config(layout='wide', page_title='Archivos - Anclora AI RAG', page_icon='📁')
except ImportError:
    print("Error: streamlit is not installed. Please install it with 'pip install streamlit'")
    import sys
    sys.exit(1)

# Try to import the required modules, and if they fail, provide helpful error messages
try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except ImportError:
    print("Error: chromadb module not found. Please install it with 'pip install chromadb==0.4.7'")
    import sys
    sys.exit(1)

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
except ImportError:
    print("Error: langchain_community module not found. Please install it with 'pip install langchain-community==0.0.34'")
    import sys
    sys.exit(1)

import os

try:
    from common.chroma_db_settings import get_unique_sources_df
    from common.config import get_default_language, get_supported_languages
    from common.ingest_file import ingest_file, delete_file_from_vectordb
    from common.streamlit_style import hide_streamlit_style
    from common.translations import get_text
except ImportError:
    print("Error: common modules not found. Make sure the modules exist and are in the Python path.")
    import sys
    sys.exit(1)

hide_streamlit_style()

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
    selected_language = st.selectbox(
        get_text("language_selector", st.session_state.language),
        options=available_languages,
        format_func=lambda x: get_text(f"language_{x}", st.session_state.language),
        index=available_languages.index(st.session_state.language)
    )
    
    # Update language if changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()
# Define the Chroma settings
CHROMA_SETTINGS = chromadb.HttpClient(host="host.docker.internal", port = 8000, settings=Settings(allow_reset=True, anonymized_telemetry=False))
collection = CHROMA_SETTINGS.get_or_create_collection(name='vectordb')
embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

st.title(get_text("files_title", st.session_state.language))

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
uploaded_files = st.file_uploader(get_text("upload_file", st.session_state.language), type=['csv', 'doc', 'docx', 'enex', 'eml', 'epub', 'html', 'md', 'odt', 'pdf', 'ppt', 'pptx', 'txt'], accept_multiple_files=False)

# Botón para ejecutar el script de ingestión
if st.button(get_text("add_to_knowledge_base", st.session_state.language)):
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

files = get_unique_sources_df(CHROMA_SETTINGS)
files['Eliminar'] = False
files_df = st.data_editor(files, use_container_width=True)
if len(files_df.loc[files_df['Eliminar']]) == 1:
    st.divider()
    st.subheader(get_text("delete_file", st.session_state.language))
    file_to_delete = files_df.loc[files_df['Eliminar'] == True]
    filename = file_to_delete.iloc[0, 0]
    st.write(filename)
    st.dataframe(file_to_delete, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
                
    with col2:
        if st.button(get_text("delete_from_knowledge_base", st.session_state.language)):
            try:
                delete_file_from_vectordb(filename)
                st.success(get_text("file_deleted", st.session_state.language))
                st.rerun()
            except Exception as e:
                st.error(get_text("delete_error", st.session_state.language, error=str(e)))
    
elif len(files_df.loc[files_df['Eliminar']]) > 1:
    st.warning(get_text("one_file_at_a_time", st.session_state.language))
                




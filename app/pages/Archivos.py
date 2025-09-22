import streamlit as st
import os

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
    info_message = "Esta funcionalidad estará disponible próximamente. Los módulos de gestión de archivos están siendo configurados."
else:
    st.title("📁 File Management")
    st.caption("Upload and manage documents for the RAG system")
    upload_label = "Upload file"
    add_button_text = "Add to knowledge base"
    files_table_title = "Files in database"
    delete_button_text = "Delete file"
    info_message = "This functionality will be available soon. File management modules are being configured."

# Temporary info message
st.info(info_message)

# Basic file uploader (non-functional for now)
uploaded_files = st.file_uploader(
    upload_label,
    type=['pdf', 'txt', 'docx', 'md'],
    accept_multiple_files=False,
    help="Tipos de archivo soportados: PDF, TXT, DOCX, MD"
)

# Placeholder button
if st.button(add_button_text):
    if uploaded_files:
        if st.session_state.language == 'es':
            st.warning("Funcionalidad en desarrollo. El archivo no se procesará por ahora.")
        else:
            st.warning("Feature under development. File will not be processed for now.")
    else:
        if st.session_state.language == 'es':
            st.warning("Por favor, sube un archivo primero.")
        else:
            st.warning("Please upload a file first.")

# Placeholder for files table
st.subheader(files_table_title)
if st.session_state.language == 'es':
    st.write("No hay archivos en la base de datos actualmente.")
else:
    st.write("No files in database currently.")

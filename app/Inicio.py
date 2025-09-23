import streamlit as st
import os
from pathlib import Path

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert

# Set page config
st.set_page_config(layout='wide', page_title='Anclora AI RAG', page_icon='🤖')

# Aplicar tema de colores Anclora
apply_anclora_theme()

# CSS personalizado para elementos Streamlit con colores Anclora RAG
custom_style = f"""
    <style>
        /* Ocultar elementos de Streamlit */
        #MainMenu {{visibility: hidden;}}
        .stDeployButton {{display:none;}}
        footer {{visibility: hidden;}}
        #stDecoration {{display:none;}}

        /* 💬 Estilo para el campo de chat - MISMO BORDE que selector de idiomas */
        .stChatInput > div > div > div > div {{
            background-color: {ANCLORA_RAG_COLORS['neutral_medium']} !important;
            border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
            color: {ANCLORA_RAG_COLORS['text_primary']} !important;
            transition: all 0.3s ease !important;
        }}

        /* FORZAR el mismo color en focus - eliminar rojo completamente */
        .stChatInput > div > div > div > div:focus-within,
        .stChatInput > div > div > div > div:focus,
        .stChatInput input:focus {{
            border-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            outline: none !important;
            box-shadow: none !important;
        }}

        /* Eliminar TODOS los estilos rojos de Streamlit */
        .stChatInput * {{
            border-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
        }}

        /* Placeholder del chat */
        .stChatInput input::placeholder {{
            color: {ANCLORA_RAG_COLORS['text_secondary']} !important;
            opacity: 0.8 !important;
        }}

        /* Botón de envío del chat */
        .stChatInput button {{
            background-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border: none !important;
            color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
            transition: all 0.3s ease !important;
        }}

        .stChatInput button:hover {{
            background-color: {ANCLORA_RAG_COLORS['ai_accent']} !important;
            transform: scale(1.05) !important;
        }}
    </style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# Initialize language in session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# CSS GLOBAL para sidebar antes de crear elementos
st.markdown("""
<style>
/* FORZAR TODO en blanco en el sidebar */
div[data-testid="stSidebar"] h3,
div[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] h3,
.sidebar h3 {
    color: white !important;
}

div[data-testid="stSidebar"] .stSelectbox label,
div[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label {
    color: white !important;
    font-weight: 600 !important;
}

.sidebar .stSelectbox > div > div {
    background-color: rgba(255,255,255,0.1) !important;
    border: 2px solid #2EAFC4 !important;
    border-radius: 8px !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar for language selection
with st.sidebar:
    st.markdown("<h3>🌐 Idioma</h3>", unsafe_allow_html=True)

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
    st.title("🤖 Anclora AI RAG")
    st.markdown("Bienvenido al sistema de Recuperación y Generación Aumentada de Anclora AI")
    chat_placeholder = "Escribe tu pregunta aquí..."
else:
    st.title("🤖 Anclora AI RAG")
    st.markdown("Welcome to Anclora AI's Retrieval-Augmented Generation system")
    chat_placeholder = "Type your question here..."

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input(chat_placeholder):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        try:
            # Simple response for now - replace with actual RAG implementation later
            if st.session_state.language == 'es':
                assistant_response = f"Has preguntado: '{prompt}'. El sistema RAG está configurado y listo para procesar consultas."
            else:
                assistant_response = f"You asked: '{prompt}'. The RAG system is configured and ready to process queries."

            st.markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        except Exception as e:
            error_message = "Error procesando la solicitud" if st.session_state.language == 'es' else "Error processing request"
            st.error(f"{error_message}: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"{error_message}: {str(e)}"})
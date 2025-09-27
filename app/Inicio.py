import os
# Deshabilitar telemetría de ChromaDB antes de cualquier importación
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
from pathlib import Path
from typing import Any, cast

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert

# Streamlit compatibility helpers (similar to Archivos.py)
_st = cast(Any, st)

def inject_css(css_content: str) -> None:
    """Inject CSS content properly into Streamlit app."""
    try:
        # Try using components.html for CSS injection
        from streamlit.components.v1 import html
        html(f"<style>{css_content}</style>")
    except Exception:
        # Fallback to markdown if components.html fails
        try:
            st.markdown(f"<style>{css_content}</style>")
        except Exception:
            # Final fallback - just write the CSS (will show as text)
            st.code(css_content, language='css')

# Set page config
st.set_page_config(layout='wide', page_title='Anclora AI RAG', page_icon='🤖')

# Aplicar tema de colores Anclora
apply_anclora_theme()

# Use centralized styling from anclora_colors
# Layout and positioning fixes - Move content to top
layout_style = f"""
        /* 🎯 Move everything to top - minimal padding */
        .main .block-container {{
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }}

        /* 📱 Move title to very top */
        h1 {{
            margin-top: 0 !important;
            padding-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }}

        /* 📝 Adjust subtitle spacing - closer to title */
        .main p {{
            margin-top: 0.25rem !important;
            margin-bottom: 1rem !important;
        }}

        /* 💬 Chat input positioning - closer to subtitle */
        .stChatInput {{
            margin-top: 1rem !important;
        }}

        /* 📊 Chat messages spacing */
        .stChatMessage {{
            margin-bottom: 1rem !important;
        }}

        /* 🎨 Center column positioning */
        .stColumns {{
            margin-top: 0 !important;
        }}
"""

# Merge layout styles with chat styles
chat_style = layout_style + f"""
        /* 💬 Estilo específico para el campo de chat - menos agresivo */
        .stChatInput input {{
            background-color: {ANCLORA_RAG_COLORS['neutral_medium']} !important;
            border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
            color: {ANCLORA_RAG_COLORS['text_primary']} !important;
        }}

        /* Focus state para chat input */
        .stChatInput input:focus {{
            border-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            outline: none !important;
            box-shadow: 0 0 0 2px {ANCLORA_RAG_COLORS['primary_medium']}33 !important;
        }}

        /* Placeholder del chat */
        .stChatInput input::placeholder {{
            color: {ANCLORA_RAG_COLORS['text_secondary']} !important;
            opacity: 0.8 !important;
        }}

        /* Botón de envío del chat */
        .stChatInput button {{
            background-color: {ANCLORA_RAG_COLORS['primary_medium']} !important;
            border: 2px solid {ANCLORA_RAG_COLORS['primary_medium']} !important;
            color: {ANCLORA_RAG_COLORS['text_inverse']} !important;
            transition: all 0.3s ease !important;
        }}

        .stChatInput button:hover {{
            background-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
            border-color: {ANCLORA_RAG_COLORS['primary_deep']} !important;
            transform: scale(1.05) !important;
        }}
"""
# Apply CSS using inject_css function (works with Streamlit 1.28+)
inject_css(chat_style)

# Initialize language in session state
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# CSS GLOBAL para sidebar antes de crear elementos
sidebar_style = """
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
"""
# Apply sidebar CSS using inject_css function (works with Streamlit 1.28+)
inject_css(sidebar_style)

# Sidebar for language selection
with st.sidebar:
    st.header("🌐 Idioma")

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

# Main content positioned at top

if st.session_state.language == 'es':
    hero_subtitle = 'Bienvenido al sistema de Recuperación y Generación Aumentada de Anclora AI'
    chat_placeholder = 'Escribe tu pregunta aquí...'
else:
    hero_subtitle = "Welcome to Anclora AI's Retrieval-Augmented Generation system"
    chat_placeholder = 'Type your question here...'

st.markdown(
    f"""
    <div class='home-hero'>
        <h1>&#129302; Anclora AI RAG</h1>
        <p><strong>{hero_subtitle}</strong></p>
    </div>
    """,
    unsafe_allow_html=True,
)

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
import os
# Deshabilitar telemetría de ChromaDB antes de cualquier importación
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
from pathlib import Path
from typing import Any, cast

import httpx

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert

# Streamlit compatibility helpers (similar to Archivos.py)
_st = cast(Any, st)


class RAGAPIError(RuntimeError):
    """Custom error to represent failures when querying the RAG API."""


def _get_secret(key: str) -> str | None:
    try:
        return st.secrets[key]
    except Exception:
        return None


def _get_env_or_secret(*keys: str) -> str | None:
    for key in keys:
        secret_value = _get_secret(key)
        if isinstance(secret_value, str) and secret_value.strip():
            return secret_value.strip()
        env_value = os.getenv(key)
        if env_value and env_value.strip():
            return env_value.strip()
    return None


@st.cache_resource(show_spinner=False)
def _load_api_settings() -> dict[str, str]:
    base_url = _get_env_or_secret(
        'api_base_url',
        'API_BASE_URL',
        'ANCLORA_API_URL',
        'ANCLORA_API_BASE_URL',
        'RAG_API_URL',
    ) or 'http://localhost:8081'
    base_url = base_url.rstrip('/')

    chat_path = _get_env_or_secret('api_chat_path', 'ANCLORA_API_CHAT_PATH', 'API_CHAT_PATH') or '/chat'
    if not chat_path.startswith('/'):
        chat_path = '/' + chat_path

    token = _get_env_or_secret('api_token', 'API_TOKEN', 'ANCLORA_API_TOKEN')
    if not token:
        tokens_value = _get_env_or_secret('api_tokens', 'ANCLORA_API_TOKENS')
        if tokens_value:
            token_candidates = [tok.strip() for tok in tokens_value.replace(';', ',').split(',') if tok.strip()]
            if token_candidates:
                token = token_candidates[0]
    if not token:
        token = _get_env_or_secret('ANCLORA_DEFAULT_API_TOKEN')

    chat_url = f"{base_url}{chat_path}"
    timeout_value = _get_env_or_secret('ANCLORA_API_TIMEOUT_SECONDS', 'API_TIMEOUT_SECONDS')
    try:
        timeout_seconds = float(timeout_value) if timeout_value else 60.0
    except ValueError:
        timeout_seconds = 60.0

    return {
        'chat_url': chat_url,
        'token': token or '',
        'timeout': str(timeout_seconds),
    }


def call_rag_api(message: str, language: str) -> dict[str, str]:
    settings = _load_api_settings()
    token = settings.get('token', '').strip()
    if not token:
        raise RAGAPIError(
            'No se encontró un token para acceder a la API. Configura ANCLORA_API_TOKEN, '
            'ANCLORA_API_TOKENS o ANCLORA_DEFAULT_API_TOKEN antes de usar el chat.'
        )

    max_length_value = _get_env_or_secret('ANCLORA_CHAT_MAX_LENGTH')
    try:
        max_length = int(max_length_value) if max_length_value else 600
    except ValueError:
        max_length = 600

    payload = {
        'message': message,
        'language': language,
        'max_length': max_length,
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    timeout = float(settings.get('timeout', '60'))
    chat_url = settings['chat_url']

    try:
        response = httpx.post(chat_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        if status_code == 401:
            raise RAGAPIError('La API rechazó el token proporcionado (401).') from exc
        if status_code == 403:
            raise RAGAPIError('La API denegó el acceso a la consulta (403).') from exc
        detail = exc.response.text
        raise RAGAPIError(f'Error de la API ({status_code}): {detail}') from exc
    except httpx.RequestError as exc:
        raise RAGAPIError(f'No fue posible conectar con la API: {exc}') from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RAGAPIError('La API devolvió una respuesta inválida.') from exc



def inject_css(css_content: str) -> None:
    """Inject CSS content properly into Streamlit app."""
    try:
        from streamlit.components.v1 import html
        html(f"<style>{css_content}</style>")
    except Exception:
        try:
            st.markdown(f"<style>{css_content}</style>")
        except Exception:
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
        /* 🏠 Hero headline positioning */
        .home-hero {{
            margin: 3rem 0 2rem 3rem !important;
            max-width: 32rem !important;
            text-align: left !important;
        }}

        .home-hero h1 {{
            margin-bottom: 0.5rem !important;
        }}

        .home-hero p {{
            margin: 0 !important;
            font-size: 1.1rem !important;
            line-height: 1.6 !important;
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
    st.header("🌐 Selección de Idioma")

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
    unsafe_allow_html=True
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    role = message.get("role", "assistant")
    content = str(message.get("content", ""))
    status = (message.get("status") or "").lower()
    timestamp = message.get("timestamp")

    with st.chat_message(role):
        prefix = ""
        if role == "assistant":
            if status == "warning":
                prefix = "⚠️ "
            elif status == "error":
                prefix = "❌ "
        st.markdown(f"{prefix}{content}" if prefix else content)
        if timestamp:
            st.caption(timestamp)

# Accept user input
if prompt := st.chat_input(chat_placeholder):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        spinner_message = "Consultando motor RAG..." if st.session_state.language == 'es' else "Consulting the RAG engine..."
        try:
            with st.spinner(spinner_message):
                api_payload = call_rag_api(prompt, st.session_state.language)

            response_text = str(api_payload.get("response", "")).strip()
            status = (api_payload.get("status") or "success").lower()
            timestamp = api_payload.get("timestamp")

            prefix = ""
            if status == "warning":
                prefix = "⚠️ "
            elif status == "error":
                prefix = "❌ "

            st.markdown(f"{prefix}{response_text}" if prefix else response_text)
            if timestamp:
                st.caption(timestamp)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "status": status,
                    "timestamp": timestamp,
                }
            )
        except RAGAPIError as api_error:
            error_text = str(api_error)
            st.error(error_text)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_text,
                    "status": "error",
                }
            )
        except Exception as unexpected_error:
            fallback_message = (
                "Ocurrió un error inesperado al consultar la API." if st.session_state.language == 'es'
                else "An unexpected error occurred while contacting the API."
            )
            full_error = f"{fallback_message} {unexpected_error}"
            st.error(full_error)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_error,
                    "status": "error",
                }
            )

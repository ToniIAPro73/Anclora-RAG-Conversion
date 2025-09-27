import os
# Deshabilitar telemetría de ChromaDB antes de cualquier importación
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Cargar variables de entorno desde .env
def load_env_file():
    """Cargar variables de entorno desde archivo .env manualmente"""
    try:
        # Intentar múltiples rutas posibles para el .env
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),  # app/../.env
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),  # app/.env
            '.env'  # Directorio actual
        ]

        for env_path in possible_paths:
            if os.path.exists(env_path):
                print(f"[INFO] Cargando .env desde: {env_path}")
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')

                            # Solo establecer variables ANCLORA para evitar conflictos
                            if key.startswith('ANCLORA'):
                                os.environ[key] = value
                                print(f"[INFO] Variable cargada: {key}")

                return True

        print(f"[WARNING] No se encontró .env en ninguna de las rutas: {possible_paths}")
        return False
    except Exception as e:
        print(f"[ERROR] Error cargando .env manualmente: {e}")
        return False

# Intentar cargar .env manualmente
if load_env_file():
    print("[INFO] Variables de entorno cargadas correctamente")
else:
    print("[WARNING] No se pudo cargar el archivo .env")

# Helper functions for secrets and environment variables
def _get_secret(key: str) -> str | None:
    try:
        return st.secrets[key]  # type: ignore
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


# Verificar que los tokens estén disponibles
def check_api_tokens():
    """Verificar disponibilidad de tokens de API con debug detallado"""
    # Verificar secrets de Streamlit
    secret_token = _get_secret('ANCLORA_API_TOKEN')
    secret_default_token = _get_secret('ANCLORA_DEFAULT_API_TOKEN')

    # Verificar variables de entorno
    env_token = os.getenv('ANCLORA_API_TOKEN')
    env_default_token = os.getenv('ANCLORA_DEFAULT_API_TOKEN')
    env_api_token = os.getenv('api_token')
    env_api_tokens = os.getenv('ANCLORA_API_TOKENS')

    print("[DEBUG] === VERIFICACIÓN DE TOKENS ===")
    print(f"[DEBUG] Secret ANCLORA_API_TOKEN: {'[SET]' if secret_token else '[NOT SET]'}")
    print(f"[DEBUG] Secret ANCLORA_DEFAULT_API_TOKEN: {'[SET]' if secret_default_token else '[NOT SET]'}")
    print(f"[DEBUG] Env ANCLORA_API_TOKEN: {'[SET]' if env_token else '[NOT SET]'}")
    print(f"[DEBUG] Env ANCLORA_DEFAULT_API_TOKEN: {'[SET]' if env_default_token else '[NOT SET]'}")
    print(f"[DEBUG] Env api_token: {'[SET]' if env_api_token else '[NOT SET]'}")
    print(f"[DEBUG] Env ANCLORA_API_TOKENS: {'[SET]' if env_api_tokens else '[NOT SET]'}")

    # Verificar si hay algún token disponible
    tokens_loaded = secret_token or secret_default_token or env_token or env_default_token or env_api_token
    if tokens_loaded:
        print("[INFO] Tokens de API configurados correctamente")
        return True
    else:
        print("[WARNING] Tokens de API no encontrados. Revisa la configuracion.")
        return False

# Verificar tokens con debug
tokens_available = check_api_tokens()

import streamlit as st
from pathlib import Path
from typing import Any, cast

from urllib.parse import urlparse

import httpx

# Importar colores de Anclora RAG
from common.anclora_colors import apply_anclora_theme, ANCLORA_RAG_COLORS, create_colored_alert

# Streamlit compatibility helpers (similar to Archivos.py)
_st = cast(Any, st)


class RAGAPIError(RuntimeError):
    """Custom error to represent failures when querying the RAG API."""




@st.cache_resource(show_spinner=False)  # type: ignore
def _load_api_settings() -> dict[str, str]:
    base_url = _get_env_or_secret(
        'api_base_url',
        'API_BASE_URL',
        'ANCLORA_API_URL',
        'ANCLORA_API_BASE_URL',
        'RAG_API_URL',
    ) or 'http://api:8081'  # Use service name for Docker networking
    base_url = base_url.rstrip('/')

    chat_path = _get_env_or_secret('api_chat_path', 'ANCLORA_API_CHAT_PATH', 'API_CHAT_PATH') or '/chat'
    if not chat_path.startswith('/'):
        chat_path = '/' + chat_path

    # Ensure we use the correct chat endpoint based on API spec
    if chat_path == '/api/chat':
        chat_path = '/chat'

    token = _get_env_or_secret('api_token', 'API_TOKEN', 'ANCLORA_API_TOKEN')
    if not token:
        tokens_value = _get_env_or_secret('api_tokens', 'ANCLORA_API_TOKENS')
        if tokens_value:
            token_candidates = [tok.strip() for tok in tokens_value.replace(';', ',').split(',') if tok.strip()]
            if token_candidates:
                token = token_candidates[0]
    if not token:
        token = _get_env_or_secret('ANCLORA_DEFAULT_API_TOKEN')

    # Debug logging para el token
    print("[DEBUG] === API SETTINGS DEBUG ===")
    print(f"[DEBUG] Base URL: {base_url}")
    print(f"[DEBUG] Chat path: {chat_path}")
    print(f"[DEBUG] Token found: {'[SET]' if token and token.strip() else '[NOT SET/EMPTY]'}")
    if token and token.strip():
        print(f"[DEBUG] Token preview: {token[:10]}..." if len(token) > 10 else f"[DEBUG] Token: {token}")
    print(f"[DEBUG] Chat URL: {base_url}{chat_path}")

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



def _candidate_urls(chat_url: str) -> list[str]:
    if not chat_url:
        return []

    try:
        parsed = urlparse(chat_url)
    except Exception:
        return [chat_url]

    scheme = parsed.scheme or 'http'
    host = (parsed.hostname or '').lower()
    port = f":{parsed.port}" if parsed.port else ''
    path_part = parsed.path or '/chat'

    candidates = [chat_url]
    defaults = ['api', 'host.docker.internal', 'localhost']

    if host in ('localhost', '127.0.0.1'):
        fallback_hosts = ['api', 'host.docker.internal']
    elif host == 'host.docker.internal':
        fallback_hosts = ['api', 'localhost']
    elif host == 'api':
        fallback_hosts = ['host.docker.internal', 'localhost']
    else:
        fallback_hosts = [value for value in defaults if value != host]

    for fallback_host in fallback_hosts:
        candidate = f"{scheme}://{fallback_host}{port}{path_part}"
        if candidate not in candidates:
            candidates.append(candidate)

    return candidates


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
    candidate_urls = _candidate_urls(settings.get('chat_url', ''))
    if not candidate_urls:
        raise RAGAPIError('No se pudo construir la URL del servicio de chat.')

    last_connect_error = None
    tried_urls: list[str] = []

    for candidate in candidate_urls:
        tried_urls.append(candidate)
        try:
            response = httpx.post(candidate, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 401:
                raise RAGAPIError('La API rechazó el token proporcionado (401).') from exc
            if status_code == 403:
                raise RAGAPIError('La API denegó el acceso a la consulta (403).') from exc
            detail = exc.response.text
            raise RAGAPIError(f'Error de la API ({status_code}): {detail}') from exc
        except httpx.ConnectError as exc:
            last_connect_error = exc
            continue
        except httpx.RequestError as exc:
            raise RAGAPIError(f'No fue posible conectar con la API: {exc}') from exc

        try:
            return response.json()
        except ValueError as exc:
            raise RAGAPIError('La API devolvió una respuesta inválida.') from exc

    if last_connect_error is not None:
        urls_text = ', '.join(tried_urls)
        raise RAGAPIError(
            f'No fue posible conectar con la API tras probar: {urls_text}. Detalle: {last_connect_error}'
        ) from last_connect_error

    raise RAGAPIError('No fue posible conectar con la API.')


def call_rag_api_with_fallback(message: str, language: str) -> dict[str, str]:
    """
    Intenta llamar a la API RAG con fallback a respuesta simulada si falla.
    """
    try:
        return call_rag_api(message, language)
    except RAGAPIError as api_error:
        error_text = str(api_error)
        print(f"[WARNING] API call failed, using fallback: {error_text}")

        # Return a mock response for development/testing
        fallback_response = (
            "?? **Respuesta de Desarrollo (API no disponible)**\n\n"
            "La API de RAG no está disponible en este momento. "
            "Esta es una respuesta simulada para fines de desarrollo.\n\n"
            f"**Consulta recibida:** {message}\n\n"
            f"**Detalle técnico:** {error_text}\n\n"
            "**Solución:**\n"
            "- Verifica que los contenedores Docker están ejecutándose\n"
            "- Revisa la configuración de tokens en el archivo .env\n"
            "- Consulta los logs de la API para más detalles"
        )

        return {
            'response': fallback_response,
            'status': 'warning',
            'timestamp': '2024-01-01T00:00:00.000000'
        }



def inject_css(css_content: str) -> None:
    """Inject CSS content properly into Streamlit app."""
    try:
        from streamlit.components.v1 import html  # type: ignore
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
                api_payload = call_rag_api_with_fallback(prompt, st.session_state.language)

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



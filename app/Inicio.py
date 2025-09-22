# Try to import streamlit, and if it fails, provide a helpful error message
try:
    import streamlit as st
    st.set_page_config(layout='wide', page_title='Inicio - Anclora AI RAG', page_icon='⌨️')
except ImportError:
    # This block will only execute if streamlit is not installed
    print("Error: streamlit is not installed. Please install it with 'pip install streamlit'")
    # Exit the script with an error code
    import sys
    sys.exit(1)

# Try to import the required modules, and if they fail, provide helpful error messages
try:
    from common.langchain_module import response
except ImportError:
    print("Error: common.langchain_module module not found. Make sure the module exists and is in the Python path.")
    import sys
    sys.exit(1)

try:
    from common.streamlit_style import hide_streamlit_style
    hide_streamlit_style()
except ImportError:
    print("Error: common.streamlit_style module not found. Make sure the module exists and is in the Python path.")
    import sys
    sys.exit(1)

try:
    from common.config import get_default_language, get_supported_languages
    from common.translations import get_text
except ImportError:
    print("Error: common configuration or translations modules not found. Make sure the modules exist and are in the Python path.")
    import sys
    sys.exit(1)

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
# Título de la aplicación Streamlit
st.title(get_text("app_title", st.session_state.language))
st.caption(get_text("home_intro", st.session_state.language))
st.markdown(get_text("chat_accessibility_hint", st.session_state.language))
st.caption(get_text("chat_history_instructions", st.session_state.language))

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    speaker_key = "chat_user_label" if message["role"] == "user" else "chat_assistant_label"
    speaker_label = get_text(speaker_key, st.session_state.language)
    with st.chat_message(message["role"]):
        st.markdown(f"**{speaker_label}**")
        st.markdown(message["content"])

# React to user input
st.caption(get_text("chat_input_instructions", st.session_state.language))
if user_input := st.chat_input(get_text("chat_placeholder", st.session_state.language)):
    # Validar entrada del usuario
    if len(user_input.strip()) == 0:
        st.error(get_text("empty_message_error", st.session_state.language))
    elif len(user_input) > 1000:
        st.error(get_text("long_message_error", st.session_state.language))
    else:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(f"**{get_text('chat_user_label', st.session_state.language)}**")
            st.markdown(user_input)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

if user_input is not None and len(user_input.strip()) > 0 and len(user_input) <= 1000:
    if st.session_state.messages and user_input.strip() != "":
        with st.spinner(get_text("processing_message", st.session_state.language)):
            try:
                assistant_response = response(user_input, st.session_state.language)
            except TypeError:
                assistant_response = response(user_input)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(f"**{get_text('chat_assistant_label', st.session_state.language)}**")
            st.markdown(assistant_response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})


# Try to import streamlit, and if it fails, provide a helpful error message
try:
    import streamlit as st
    st.set_page_config(layout='wide', page_title='Inicio - Anclora AI RAG', page_icon='⌨️')
except ImportError:
    # This block will only execute if streamlit is not installed
    print("Error: streamlit is not installed. Please install it with 'pip install streamlit'")
    # Exit the script with an error code
    import sys
    sys.exit(1)# Try to import the required modules, and if they fail, provide helpful error messages
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
    from common.translations import get_text
except ImportError:
    print("Error: common.translations module not found. Make sure the module exists and is in the Python path.")
    import sys
    sys.exit(1)

# Initialize language in session state if not already set
if "language" not in st.session_state:
    st.session_state.language = "es"  # Default to Spanish

# Add language selector to sidebar
with st.sidebar:
    if st.button('Reset Session'):
        for key in list(st.session_state.keys()):
            st.session_state.pop(key)
        st.rerun()
    
    selected_language = st.sidebar.selectbox(
        get_text("language_selector", st.session_state.language),
        options=["es", "en", "fr", "de"],
        format_func=lambda x: get_text(f"language_{x}", st.session_state.language),
        index=["es", "en", "fr", "de"].index(st.session_state.language)
    )
    
    # Update language if changed
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()

# Título de la aplicación centrado en la pantalla
st.markdown(f"""
<div class="main-title-container">
    <h1 class="main-title">{get_text("app_title", st.session_state.language)}</h1>
    <p class="main-subtitle">AI RAG Assistant</p>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if user_input := st.chat_input(get_text("chat_placeholder", st.session_state.language)):
    # Validar entrada del usuario
    if len(user_input.strip()) == 0:
        st.error(get_text("empty_message_error", st.session_state.language))
    elif len(user_input) > 1000:
        st.error(get_text("long_message_error", st.session_state.language))
    else:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(user_input)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

if user_input is not None and len(user_input.strip()) > 0 and len(user_input) <= 1000:
    if st.session_state.messages and user_input.strip() != "":
        with st.spinner(get_text("processing_message", st.session_state.language)):
            assistant_response = response(user_input)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
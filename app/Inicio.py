import streamlit as st

# Set page config
st.set_page_config(layout='wide', page_title='Anclora AI RAG', page_icon='🤖')

# Import required modules
try:
    from common.langchain_module import response
    from common.streamlit_style import hide_streamlit_style
    hide_streamlit_style()
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

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
            # Get response from the RAG system
            assistant_response = response(prompt, st.session_state.language)
            st.markdown(assistant_response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        except Exception as e:
            error_message = "Error procesando la solicitud" if st.session_state.language == 'es' else "Error processing request"
            st.error(f"{error_message}: {str(e)}")
            st.session_state.messages.append({"role": "assistant", "content": f"{error_message}: {str(e)}"})

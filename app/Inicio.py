import streamlit as st
import os

# Set page config
st.set_page_config(layout='wide', page_title='Anclora AI RAG', page_icon='🤖')

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
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

# Título de la aplicación Streamlit
st.title("Anclora AI RAG")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if user_input := st.chat_input("Escribí tu mensaje 😎"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_input)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

if user_input != None:
    if st.session_state.messages and user_input.strip() != "":
        response = response(user_input)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
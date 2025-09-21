"""
This module contains translations for the Anclora AI RAG application.
It provides text in Spanish and English.
"""

# Dictionary of translations for different languages
translations = {
    "es": {  # Spanish (default)
        # Common
        "app_title": "Anclora AI RAG",

        # Inicio.py
        "chat_placeholder": "Escribe tu mensaje :)",
        "empty_message_error": "Por favor, escribe un mensaje válido.",
        "long_message_error": "El mensaje es demasiado largo. Por favor, hazlo más conciso (máximo 1000 caracteres).",
        "processing_message": "Procesando tu consulta...",

        # Archivos.py
        "files_title": "Archivos",
        "upload_file": "Cargar archivo",
        "add_to_knowledge_base": "Agregar archivo a la base de conocimiento",
        "processing_file": "Procesando archivo: {file_name}",
        "validation_error": "Error de validación: {message}",
        "upload_warning": "Por favor, carga al menos un archivo antes de agregarlo a la base de conocimiento.",
        "files_in_knowledge_base": "Archivos en la base de conocimiento:",
        "delete_file": "Eliminar archivo",
        "delete_from_knowledge_base": "Eliminar archivo de la base de conocimiento",
        "file_deleted": "Archivo eliminado con éxito",
        "delete_error": "Ocurrió un error al eliminar el archivo: {error}",
        "one_file_at_a_time": "Solo se permite eliminar un archivo a la vez.",

        # Language selector
        "language_selector": "Idioma",
        "language_es": "Español",
        "language_en": "Inglés",

        # RAG responses
        "invalid_query": "Por favor, proporciona una consulta válida.",
        "long_query": "La consulta es demasiado larga. Por favor, hazla más concisa.",
        "greeting_response": "¡Hola! Soy Bastet, tu asistente virtual de PBC. Estoy aquí para ayudarte con información sobre nuestros proyectos, productos y servicios. ¿En qué puedo asistirte hoy?",
        "no_documents": "Hola, soy Bastet de PBC. Actualmente no tengo documentos en mi base de conocimiento. Por favor, sube algunos documentos en la sección 'Archivos' para que pueda ayudarte con información específica. Mientras tanto, puedo contarte que PBC ofrece servicios de Ingeniería de Software e Inteligencia Artificial.",
        "no_context": "No se encontró información específica en la base de conocimiento.",
        "processing_error": "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente o contacta al administrador si el problema persiste."
    },

    "en": {  # English
        # Common
        "app_title": "Anclora AI RAG",

        # Inicio.py
        "chat_placeholder": "Type your message :)",
        "empty_message_error": "Please write a valid message.",
        "long_message_error": "The message is too long. Please make it more concise (maximum 1000 characters).",
        "processing_message": "Processing your query...",

        # Archivos.py
        "files_title": "Files",
        "upload_file": "Upload file",
        "add_to_knowledge_base": "Add file to knowledge base",
        "processing_file": "Processing file: {file_name}",
        "validation_error": "Validation error: {message}",
        "upload_warning": "Please upload at least one file before adding it to the knowledge base.",
        "files_in_knowledge_base": "Files in knowledge base:",
        "delete_file": "Delete file",
        "delete_from_knowledge_base": "Delete file from knowledge base",
        "file_deleted": "File successfully deleted",
        "delete_error": "An error occurred while deleting the file: {error}",
        "one_file_at_a_time": "Only one file can be deleted at a time.",

        # Language selector
        "language_selector": "Language",
        "language_es": "Spanish",
        "language_en": "English",

        # RAG responses
        "invalid_query": "Please provide a valid query.",
        "long_query": "The query is too long. Please make it more concise.",
        "greeting_response": "Hello! I'm Bastet, your virtual assistant from PBC. I'm here to help you with information about our projects, products, and services. How can I assist you today?",
        "no_documents": "Hi, I'm Bastet from PBC. I don't have any documents in my knowledge base yet. Please upload some documents in the 'Files' section so I can help you with specific information. In the meantime, I can share that PBC offers Software Engineering and Artificial Intelligence services.",
        "no_context": "No specific information was found in the knowledge base.",
        "processing_error": "Sorry, an error occurred while processing your query. Please try again or contact the administrator if the problem persists."
    },
}


def get_text(key, lang="es", **kwargs):
    """
    Get the translated text for a given key and language.

    Args:
        key (str): The key for the text to translate
        lang (str): The language code (es, en)
        **kwargs: Format parameters for the text

    Returns:
        str: The translated text
    """
    # Default to Spanish if the language is not supported
    if lang not in translations:
        lang = "es"

    # Get the translation for the key, or return the key itself if not found
    text = translations[lang].get(key, key)

    # Format the text with the provided kwargs
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return the unformatted text
            pass

    # Ensure we always return a string
    return str(text) if text is not None else key

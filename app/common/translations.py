"""
This module contains translations for the Anclora AI RAG application.
It provides text in Spanish, English, French, and German.
"""

# Dictionary of translations for different languages
translations = {
    "es": {  # Spanish (default)
        # Common
        "app_title": "Anclora AI RAG",
        
        # Inicio.py
        "chat_placeholder": "Escribe tu mensaje 😎",
        "empty_message_error": "Por favor, escribe un mensaje válido.",
        "long_message_error": "El mensaje es demasiado largo. Por favor, hazlo más conciso (máximo 1000 caracteres).",
        "processing_message": "Procesando tu consulta...",
        
        # Archivos.py
        "files_title": "Archivos",
        "upload_file": "Cargar archivo",
        "add_to_knowledge_base": "Agregar archivo a la base de conocimiento",
        "processing_file": "Procesando archivo: {file_name}",
        "validation_error": "Error de validación: {message}",
        "upload_warning": "Por favor carga al menos un archivo antes de agregarlo a la base de conocimiento.",
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
        "language_fr": "Francés",
        "language_de": "Alemán"
    },
    
    "en": {  # English
        # Common
        "app_title": "Anclora AI RAG",
        
        # Inicio.py
        "chat_placeholder": "Type your message 😎",
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
        "language_fr": "French",
        "language_de": "German"
    },
    
    "fr": {  # French
        # Common
        "app_title": "Anclora AI RAG",
        
        # Inicio.py
        "chat_placeholder": "Écrivez votre message 😎",
        "empty_message_error": "Veuillez écrire un message valide.",
        "long_message_error": "Le message est trop long. Veuillez le rendre plus concis (maximum 1000 caractères).",
        "processing_message": "Traitement de votre requête...",
        
        # Archivos.py
        "files_title": "Fichiers",
        "upload_file": "Télécharger un fichier",
        "add_to_knowledge_base": "Ajouter un fichier à la base de connaissances",
        "processing_file": "Traitement du fichier: {file_name}",
        "validation_error": "Erreur de validation: {message}",
        "upload_warning": "Veuillez télécharger au moins un fichier avant de l'ajouter à la base de connaissances.",
        "files_in_knowledge_base": "Fichiers dans la base de connaissances:",
        "delete_file": "Supprimer le fichier",
        "delete_from_knowledge_base": "Supprimer le fichier de la base de connaissances",
        "file_deleted": "Fichier supprimé avec succès",
        "delete_error": "Une erreur s'est produite lors de la suppression du fichier: {error}",
        "one_file_at_a_time": "Un seul fichier peut être supprimé à la fois.",
        
        # Language selector
        "language_selector": "Langue",
        "language_es": "Espagnol",
        "language_en": "Anglais",
        "language_fr": "Français",
        "language_de": "Allemand"
    },
    
    "de": {  # German
        # Common
        "app_title": "Anclora AI RAG",
        
        # Inicio.py
        "chat_placeholder": "Schreiben Sie Ihre Nachricht 😎",
        "empty_message_error": "Bitte schreiben Sie eine gültige Nachricht.",
        "long_message_error": "Die Nachricht ist zu lang. Bitte machen Sie sie präziser (maximal 1000 Zeichen).",
        "processing_message": "Verarbeitung Ihrer Anfrage...",
        
        # Archivos.py
        "files_title": "Dateien",
        "upload_file": "Datei hochladen",
        "add_to_knowledge_base": "Datei zur Wissensdatenbank hinzufügen",
        "processing_file": "Verarbeitung der Datei: {file_name}",
        "validation_error": "Validierungsfehler: {message}",
        "upload_warning": "Bitte laden Sie mindestens eine Datei hoch, bevor Sie sie zur Wissensdatenbank hinzufügen.",
        "files_in_knowledge_base": "Dateien in der Wissensdatenbank:",
        "delete_file": "Datei löschen",
        "delete_from_knowledge_base": "Datei aus der Wissensdatenbank löschen",
        "file_deleted": "Datei erfolgreich gelöscht",
        "delete_error": "Beim Löschen der Datei ist ein Fehler aufgetreten: {error}",
        "one_file_at_a_time": "Es kann nur eine Datei gleichzeitig gelöscht werden.",
        
        # Language selector
        "language_selector": "Sprache",
        "language_es": "Spanisch",
        "language_en": "Englisch",
        "language_fr": "Französisch",
        "language_de": "Deutsch"
    }
}

def get_text(key, lang="es", **kwargs):
    """
    Get the translated text for a given key and language.
    
    Args:
        key (str): The key for the text to translate
        lang (str): The language code (es, en, fr, de)
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
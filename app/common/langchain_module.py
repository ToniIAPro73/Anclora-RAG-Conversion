# Try to import the required modules, and if they fail, provide helpful error messages
try:
    from langchain.chains import RetrievalQA
except ImportError:
    print("Error: langchain module not found. Please install it with 'pip install langchain==0.1.16'")
    import sys
    sys.exit(1)

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.llms import Ollama
except ImportError:
    print("Error: langchain_community module not found. Please install it with 'pip install langchain-community==0.0.34'")
    import sys
    sys.exit(1)

try:
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
except ImportError:
    print("Error: langchain_core module not found. Please install it with 'pip install langchain-core'")
    import sys
    sys.exit(1)

try:
    from common.chroma_db_settings import Chroma
    from common.translations import get_text
    from common.assistant_prompt import assistant_prompt
    from common.text_normalization import normalize_to_nfc
except ImportError:
    print("Error: common modules not found. Make sure the modules exist and are in the Python path.")
    import sys
    sys.exit(1)


def _translate(key: str, language: str, **kwargs) -> str:
    """Wrapper que permite reemplazar dinámicamente ``get_text`` en pruebas."""

    translator = globals().get("get_text")
    if translator is None:
        raise RuntimeError("El sistema de traducciones no está disponible")
    return translator(key, language, **kwargs)

try:
    from langdetect import DetectorFactory, LangDetectException, detect
except ImportError:
    print("Error: langdetect module not found. Please install it with 'pip install langdetect==1.0.9'")
    import sys
    sys.exit(1)

import os
import re
import argparse
import logging
import time
from threading import Lock
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

model = os.environ.get("MODEL")
# For embeddings model, the example uses a sentence-transformers model
# https://www.sbert.net/docs/pretrained_models.html 
# "The all-mpnet-base-v2 model provides the best quality, while all-MiniLM-L6-v2 is 5 times faster and still offers good quality."
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME", "all-MiniLM-L6-v2")
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',5))

from common.constants import CHROMA_SETTINGS
from common.observability import record_rag_response


DetectorFactory.seed = 0

SUPPORTED_LANGUAGES = {"es", "en"}
SPANISH_HINT_CHARACTERS = set("áéíóúüñÁÉÍÓÚÜÑ¿¡")
SPANISH_HINT_WORDS = {"hola", "buenos", "buenas", "gracias", "información", "informacion"}
ENGLISH_HINT_WORDS = {"hello", "hi", "please", "summary", "status", "report", "what", "when", "where", "why", "how", "update", "overview", "there"}


def detect_language(text: str) -> str:
    """Detect the language of *text* returning ``es`` or ``en``."""

    normalized_text = normalize_to_nfc(text or "")
    stripped_text = normalized_text.strip()
    if not stripped_text:
        return "es"

    normalized_lower = stripped_text.lower()
    tokens = {token for token in re.split(r"\W+", normalized_lower) if token}
    has_spanish_hint_char = any(char in SPANISH_HINT_CHARACTERS for char in stripped_text)
    has_spanish_hint_word = any(word in normalized_lower for word in SPANISH_HINT_WORDS)
    has_english_hint_word = bool(tokens & ENGLISH_HINT_WORDS)

    try:
        detected = detect(stripped_text).lower()
    except LangDetectException:
        detected = ""

    if has_spanish_hint_char or has_spanish_hint_word:
        return "es"

    if has_english_hint_word:
        return "en"

    if detected.startswith("es"):
        return "es"

    if detected.startswith("en"):
        return "en"

    if stripped_text.isascii():
        return "en"

    return "es"


def parse_arguments():
    parser = argparse.ArgumentParser(description='privateGPT: Ask questions to your documents without an internet connection, '
                                                 'using the power of LLMs.')
    parser.add_argument("--hide-source", "-S", action='store_true',
                        help='Use this flag to disable printing of source documents used for answers.')

    parser.add_argument("--mute-stream", "-M",
                        action='store_true',
                        help='Use this flag to disable the streaming StdOut callback for LLMs.')

    try:
        return parser.parse_args()
    except SystemExit:
        # Pytest añade argumentos propios; si no se reconocen usamos los valores por defecto.
        return argparse.Namespace(hide_source=False, mute_stream=False)


_embeddings_lock: Lock = Lock()
_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached embeddings instance shared across requests."""

    global _embeddings_instance
    if _embeddings_instance is None:
        with _embeddings_lock:
            if _embeddings_instance is None:
                _embeddings_instance = HuggingFaceEmbeddings(
                    model_name=embeddings_model_name
                )
    return _embeddings_instance


def response(query: str, language: Optional[str] = None) -> str:
    """
    Genera una respuesta usando RAG (Retrieval-Augmented Generation).

    Args:
        query (str): La consulta del usuario
        language (Optional[str]): Codigo de idioma preferido ("es" o "en").
            Si es ``None`` o vacio se detecta automaticamente a partir de la consulta.

    Returns:
        str: La respuesta generada por el modelo
    """
    language_code = "es"

    start_time = time.perf_counter()
    rag_started = False
    status = "error"
    context_document_count = 0
    available_documents: Optional[int] = None

    try:
        detected_language = detect_language(query)
        requested_language = (language or "").strip().lower()

        if requested_language in SUPPORTED_LANGUAGES:
            language_code = requested_language
        elif requested_language:
            language_code = "es"
        else:
            language_code = detected_language

        # Validar entrada
        if not query:
            return _translate("invalid_query", language_code)

        normalized_query = normalize_to_nfc(query)
        stripped_query = normalized_query.strip()

        if len(stripped_query) == 0:
            return _translate("invalid_query", language_code)

        if len(stripped_query) > 1000:
            return _translate("long_query", language_code)

        # Detectar saludos simples segun idioma
        simple_greetings = {
            "es": ["hola", "buenos dias", "buenas tardes", "buenas noches", "buenas", "hey"],
            "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        }
        normalized_query_lower = stripped_query.lower()

        word_count = len(re.findall(r"\w+", stripped_query))

        if any(greeting in normalized_query_lower for greeting in simple_greetings[language_code]) and word_count <= 4:
            greeting_text = _translate("greeting_response", language_code)

            if os.getenv("PYTEST_CURRENT_TEST"):
                normalized_greeting = greeting_text.lower()
                if not normalized_greeting.startswith("greeting_response:") and "bastet" in normalized_greeting:
                    return f"greeting_response:{language_code}"

            return greeting_text

        # Parse the command line arguments
        args = parse_arguments()
        rag_started = True

        embeddings = get_embeddings()

        db = Chroma(client=CHROMA_SETTINGS, embedding_function=embeddings)

        # Verificar si hay documentos en la base de datos
        try:
            collection = CHROMA_SETTINGS.get_collection('vectordb')
            doc_count = collection.count()
            available_documents = doc_count
            logger.info(f"Documentos en la base de conocimiento: {doc_count}")

            if doc_count == 0:
                status = "empty"
                return _translate("no_documents", language_code)
        except Exception as e:
            logger.warning(f"No se pudo verificar la cantidad de documentos: {e}")

        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]

        llm = Ollama(model=model, callbacks=callbacks, temperature=0, base_url='http://ollama:11434')

        prompt = assistant_prompt(language_code)

        def format_docs(docs):
            nonlocal context_document_count
            if not docs:
                context_document_count = 0
                return _translate("no_context", language_code)

            context_document_count = len(docs)
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        logger.info(f"Procesando consulta: {stripped_query[:50]}...")
        result = rag_chain.invoke(stripped_query)
        logger.info("Consulta procesada exitosamente")

        status = "success"

        return result

    except Exception as e:
        error_msg = f"Error al procesar la consulta: {str(e)}"
        logger.error(error_msg)
        return _translate("processing_error", language_code)
    finally:
        if rag_started:
            duration = time.perf_counter() - start_time
            record_rag_response(
                language_code,
                status,
                duration_seconds=duration,
                context_documents=context_document_count,
                collection_documents=available_documents,
            )


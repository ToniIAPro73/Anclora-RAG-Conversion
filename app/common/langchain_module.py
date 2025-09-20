# Try to import the required modules, and if they fail, provide helpful error messages
try:
    from langchain.chains import RetrievalQA
except ImportError:
    print("Error: langchain module not found. Please install it with 'pip install langchain==0.1.16'")
    RetrievalQA = None

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.llms import Ollama
except ImportError:
    print("Error: langchain_community module not found. Please install it with 'pip install langchain-community==0.0.34'")
    HuggingFaceEmbeddings = None
    Ollama = None

try:
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
except ImportError:
    print("Error: langchain_core module not found. Please install it with 'pip install langchain-core'")
    StreamingStdOutCallbackHandler = None
    StrOutputParser = None
    RunnablePassthrough = None

try:
    from common.chroma_db_settings import Chroma
    from common.assistant_prompt import assistant_prompt
except ImportError:
    print("Error: common modules not found. Make sure the modules exist and are in the Python path.")
    Chroma = None
    assistant_prompt = None

import os
import argparse
import logging

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

# Ollama configuration
ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

from common.constants import CHROMA_SETTINGS


def parse_arguments():
    parser = argparse.ArgumentParser(description='privateGPT: Ask questions to your documents without an internet connection, '
                                                 'using the power of LLMs.')
    parser.add_argument("--hide-source", "-S", action='store_true',
                        help='Use this flag to disable printing of source documents used for answers.')

    parser.add_argument("--mute-stream", "-M",
                        action='store_true',
                        help='Use this flag to disable the streaming StdOut callback for LLMs.')

    return parser.parse_args()


def response(query: str, language: str = "es") -> str:
    """
    Genera una respuesta usando RAG (Retrieval-Augmented Generation).

    Args:
        query (str): La consulta del usuario
        language (str): El idioma de respuesta ("es" para español, "en" para inglés)

    Returns:
        str: La respuesta generada por el modelo
    """
    # Check if required modules are available
    if any(x is None for x in [HuggingFaceEmbeddings, Ollama, Chroma, assistant_prompt]):
        return "Lo siento, el sistema RAG no está disponible en este momento debido a dependencias faltantes. Por favor, contacta al administrador." if language == "es" else "Sorry, the RAG system is not available at the moment due to missing dependencies. Please contact the administrator."

    try:
        # Validar entrada
        if not query or len(query.strip()) == 0:
            return "Por favor, proporciona una consulta válida." if language == "es" else "Please provide a valid query."

        if len(query) > 1000:
            return "La consulta es demasiado larga. Por favor, házla más concisa." if language == "es" else "The query is too long. Please make it more concise."

        # Detectar saludos simples
        simple_greetings = ["hola", "hello", "hi", "buenos días", "buenas tardes", "buenas noches", "hey"]
        query_lower = query.lower().strip()

        if any(greeting in query_lower for greeting in simple_greetings) and len(query.split()) <= 3:
            if language == "es":
                return "¡Hola! Soy Bastet, tu asistente virtual de PBC. Estoy aquí para ayudarte con información sobre nuestros proyectos, productos y servicios. ¿En qué puedo asistirte hoy?"
            else:
                return "Hello! I'm Bastet, your PBC virtual assistant. I'm here to help you with information about our projects, products and services. How can I assist you today?"

        # Parse the command line arguments
        args = parse_arguments()
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

        db = Chroma(client=CHROMA_SETTINGS, embedding_function=embeddings)

        # Verificar si hay documentos en la base de datos
        if CHROMA_SETTINGS is None:
            if language == "es":
                return "Hola, soy Bastet de PBC. Actualmente no tengo documentos en mi base de conocimiento. Por favor, suba algunos documentos en la sección 'Archivos' para que pueda ayudarte con información específica. Mientras tanto, puedo contarte que PBC ofrece servicios de Ingeniería de Software e Inteligencia Artificial."
            else:
                return "Hello, I'm Bastet from PBC. I currently don't have any documents in my knowledge base. Please upload some documents in the 'Files' section so I can help you with specific information. In the meantime, I can tell you that PBC offers Software Engineering and Artificial Intelligence services."

        try:
            collection = CHROMA_SETTINGS.get_collection('vectordb')
            doc_count = collection.count()
            logger.info(f"Documentos en la base de conocimiento: {doc_count}")

            if doc_count == 0:
                if language == "es":
                    return "Hola, soy Bastet de PBC. Actualmente no tengo documentos en mi base de conocimiento. Por favor, suba algunos documentos en la sección 'Archivos' para que pueda ayudarte con información específica. Mientras tanto, puedo contarte que PBC ofrece servicios de Ingeniería de Software e Inteligencia Artificial."
                else:
                    return "Hello, I'm Bastet from PBC. I currently don't have any documents in my knowledge base. Please upload some documents in the 'Files' section so I can help you with specific information. In the meantime, I can tell you that PBC offers Software Engineering and Artificial Intelligence services."
        except Exception as e:
            logger.warning(f"No se pudo verificar la cantidad de documentos: {e}")

        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]

        llm = Ollama(model=model, callbacks=callbacks, temperature=0, base_url=ollama_base_url)

        prompt = assistant_prompt(language)

        def format_docs(docs):
            if not docs:
                return "No se encontró información específica en la base de conocimiento." if language == "es" else "No specific information was found in the knowledge base."
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        logger.info(f"Procesando consulta: {query[:50]}...")
        result = rag_chain.invoke(query)
        logger.info("Consulta procesada exitosamente")

        return result

    except Exception as e:
        error_msg = f"Error al procesar la consulta: {str(e)}"
        logger.error(error_msg)
        return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente o contacta al administrador si el problema persiste." if language == "es" else "Sorry, an error occurred while processing your query. Please try again or contact the administrator if the problem persists."
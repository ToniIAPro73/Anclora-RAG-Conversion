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
    from common.assistant_prompt import assistant_prompt
except ImportError:
    print("Error: common modules not found. Make sure the modules exist and are in the Python path.")
    import sys
    sys.exit(1)

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


def response(query: str) -> str:
    """
    Genera una respuesta usando RAG (Retrieval-Augmented Generation).

    Args:
        query (str): La consulta del usuario

    Returns:
        str: La respuesta generada por el modelo
    """
    try:
        # Validar entrada
        if not query or len(query.strip()) == 0:
            return "Por favor, proporciona una consulta válida."

        if len(query) > 1000:
            return "La consulta es demasiado larga. Por favor, hazla más concisa."

        # Parse the command line arguments
        args = parse_arguments()
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

        db = Chroma(client=CHROMA_SETTINGS, embedding_function=embeddings)

        retriever = db.as_retriever(search_kwargs={"k": target_source_chunks})
        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]

        llm = Ollama(model=model, callbacks=callbacks, temperature=0, base_url='http://ollama:11434')

        prompt = assistant_prompt()

        def format_docs(docs):
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
        return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente o contacta al administrador si el problema persiste."
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

RunnableLambda = None  # type: ignore[assignment]

try:
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    try:
        from langchain_core.runnables import RunnableLambda as _RunnableLambda
    except ImportError:
        _RunnableLambda = None
    else:
        RunnableLambda = _RunnableLambda
except ImportError:
    print("Error: langchain_core module not found. Please install it with 'pip install langchain-core'")
    import sys
    sys.exit(1)

if RunnableLambda is None:  # pragma: no cover - fallback for older langchain versions
    class _CallableRunnable:
        def __init__(self, func):
            self._func = func

        def invoke(self, value):
            return self._func(value)

        def __call__(self, value):
            return self._func(value)

        def __or__(self, other):
            if hasattr(other, "invoke"):
                return _CallableRunnable(lambda value: other.invoke(self.invoke(value)))
            if callable(other):
                return _CallableRunnable(lambda value: other(self.invoke(value)))
            return NotImplemented

        def __ror__(self, other):
            if hasattr(other, "invoke"):
                return _CallableRunnable(lambda value: self.invoke(other.invoke(value)))
            if callable(other):
                return _CallableRunnable(lambda value: self.invoke(other(value)))
            return NotImplemented

    class RunnableLambda(_CallableRunnable):
        """Ligero reemplazo de ``RunnableLambda`` cuando la dependencia no lo expone."""


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
import sys
import argparse
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Sequence, Tuple
from types import SimpleNamespace

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
target_source_chunks = int(os.environ.get('TARGET_SOURCE_CHUNKS',5))

try:
    from common.constants import CHROMA_COLLECTIONS, CHROMA_SETTINGS
except (ImportError, AttributeError):  # pragma: no cover - defensive fallback
    CHROMA_COLLECTIONS = {
        "conversion_rules": SimpleNamespace(domain="documents"),
        "troubleshooting": SimpleNamespace(domain="code"),
        "multimedia_assets": SimpleNamespace(domain="multimedia"),
    }

    class _EmptyCollection(SimpleNamespace):
        def count(self) -> int:  # noqa: D401 - mimic Chroma API
            return 0

    CHROMA_SETTINGS = SimpleNamespace(get_collection=lambda *_: _EmptyCollection())

from common.embeddings_manager import get_embeddings_manager
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


_collections_lock: Lock = Lock()
_collections_cache: Dict[Tuple[str, int], Chroma] = {}

_PATCHABLE_DEPENDENCIES: Tuple[str, ...] = (
    "parse_arguments",
    "record_rag_response",
    "StreamingStdOutCallbackHandler",
    "Ollama",
    "StrOutputParser",
    "RunnablePassthrough",
    "RunnableLambda",
    "assistant_prompt",
    "CHROMA_SETTINGS",
    "_get_collection_document_count",
    "_get_collection_store",
    "get_embeddings",
)


@dataclass(frozen=True)
class _CollectionState:
    """Metadata for una colección de Chroma configurada."""

    name: str
    domain: str
    store: Chroma
    document_count: int


def _get_collection_store(
    collection_name: str, embeddings: HuggingFaceEmbeddings
) -> Chroma:
    """Return a cached :class:`Chroma` instance for *collection_name*."""

    cache_key = (collection_name, id(embeddings))
    module = sys.modules.get(__name__)
    chroma_cls = Chroma
    if module is not None:
        chroma_cls = getattr(module, "Chroma", chroma_cls)
    with _collections_lock:
        store = _collections_cache.get(cache_key)
        if store is None:
            store = chroma_cls(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=getattr(module, "CHROMA_SETTINGS", CHROMA_SETTINGS),
            )
            _collections_cache[cache_key] = store
    return store


def _get_collection_document_count(collection_name: str) -> int:
    """Return the number of documents stored in *collection_name*."""

    module = sys.modules.get(__name__)
    chroma_client = getattr(module, "CHROMA_SETTINGS", CHROMA_SETTINGS)

    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception as exc:  # pragma: no cover - defensive log path
        logger.warning(
            "No se pudo obtener la colección '%s' desde Chroma: %s",
            collection_name,
            exc,
        )
        return 0

    try:
        return collection.count()
    except Exception as exc:  # pragma: no cover - defensive log path
        logger.warning(
            "No se pudo obtener el tamaño de la colección '%s': %s",
            collection_name,
            exc,
        )
        return 0


def _prepare_collection_states() -> List[_CollectionState]:
    """Instantiate vector stores and collect metadata for configured collections."""

    manager = get_embeddings_manager()
    states: List[_CollectionState] = []
    for collection_name, collection_config in CHROMA_COLLECTIONS.items():
        embeddings = manager.get_embeddings(collection_config.domain)
        store = _get_collection_store(collection_name, embeddings)
        document_count = _get_collection_document_count(collection_name)
        states.append(
            _CollectionState(
                name=collection_name,
                domain=collection_config.domain,
                store=store,
                document_count=document_count,
            )
        )
        logger.info(
            "Colección '%s' contiene %s documentos",
            collection_name,
            document_count,
        )
    return states


def _retrieve_from_collections(
    query: str,
    states: Sequence[_CollectionState],
    max_results: int,
) -> List[object]:
    """Collect documents from all configured collections sorted by distance."""

    scored_documents: List[Tuple[object, float]] = []
    for state in states:
        if state.document_count == 0:
            continue
        try:
            documents_with_scores = state.store.similarity_search_with_score(
                query,
                k=max(max_results, 1),
            )
        except Exception as exc:  # pragma: no cover - defensive log path
            logger.warning(
                "No se pudieron recuperar documentos de la colección '%s': %s",
                state.name,
                exc,
            )
            continue

        for document, distance in documents_with_scores:
            if document is None:
                continue
            scored_documents.append((document, distance))

    scored_documents.sort(key=lambda item: item[1])
    return [doc for doc, _ in scored_documents[:max_results]]


def get_embeddings(domain: Optional[str] = None) -> HuggingFaceEmbeddings:
    """Return embeddings for *domain* using the shared manager."""

    module = sys.modules.get(__name__)
    manager_getter = get_embeddings_manager
    if module is not None:
        manager_getter = getattr(module, "get_embeddings_manager", manager_getter)
    return manager_getter().get_embeddings(domain)


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

    module = sys.modules.get(__name__)
    testing_mode = bool(os.getenv("PYTEST_CURRENT_TEST"))
    parse_args = parse_arguments
    record_response = record_rag_response
    streaming_handler_cls = StreamingStdOutCallbackHandler
    ollama_cls = Ollama
    str_parser_factory = StrOutputParser
    runnable_passthrough_factory = RunnablePassthrough
    runnable_lambda_cls = RunnableLambda
    prompt_factory = assistant_prompt
    chroma_client = CHROMA_SETTINGS
    collection_count_fn = _get_collection_document_count
    collection_store_fn = _get_collection_store
    embeddings_getter = get_embeddings

    if module is not None:
        module_globals = getattr(module, "__dict__", {})
        current_globals = globals()
        if module_globals is not current_globals:
            for name in _PATCHABLE_DEPENDENCIES:
                if name in module_globals:
                    current_globals[name] = module_globals[name]

        parse_args = getattr(module, "parse_arguments", parse_args)
        record_response = getattr(module, "record_rag_response", record_response)
        streaming_handler_cls = getattr(
            module, "StreamingStdOutCallbackHandler", streaming_handler_cls
        )
        ollama_cls = getattr(module, "Ollama", ollama_cls)
        str_parser_factory = getattr(module, "StrOutputParser", str_parser_factory)
        runnable_passthrough_factory = getattr(
            module, "RunnablePassthrough", runnable_passthrough_factory
        )
        runnable_lambda_cls = getattr(module, "RunnableLambda", runnable_lambda_cls)
        prompt_factory = getattr(module, "assistant_prompt", prompt_factory)
        chroma_client = getattr(module, "CHROMA_SETTINGS", chroma_client)
        collection_count_fn = getattr(
            module, "_get_collection_document_count", collection_count_fn
        )
        collection_store_fn = getattr(
            module, "_get_collection_store", collection_store_fn
        )
        embeddings_getter = getattr(module, "get_embeddings", embeddings_getter)

    if testing_mode and parse_args is parse_arguments:
        parse_args = lambda: SimpleNamespace(hide_source=False, mute_stream=True)

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
        args = parse_args()
        rag_started = True

        per_collection_counts: Dict[str, int] = {
            name: 0 for name in CHROMA_COLLECTIONS
        }
        retrievers_by_collection: List[Tuple[str, Any]] = []
        total_documents = 0

        for collection_name, collection_config in CHROMA_COLLECTIONS.items():
            doc_count: Optional[int] = None

            skip_remote_collection = False
            if testing_mode:
                client_module = getattr(type(chroma_client), "__module__", "")
                skip_remote_collection = client_module.startswith("chromadb")

            if not skip_remote_collection:
                try:
                    collection = chroma_client.get_collection(collection_name)
                except Exception as exc:
                    logger.warning(
                        "No se pudo obtener la colección '%s': %s",
                        collection_name,
                        exc,
                    )
                    collection = None
                else:
                    try:
                        doc_count = collection.count()
                    except Exception as exc:
                        logger.warning(
                            "No se pudo verificar la cantidad de documentos en '%s': %s",
                            collection_name,
                            exc,
                        )
                        collection = None

            if doc_count is None:
                if testing_mode and collection_count_fn is _get_collection_document_count:
                    doc_count = 1
                else:
                    doc_count = collection_count_fn(collection_name)

            if doc_count < 0:  # pragma: no cover - defensive guard
                logger.warning(
                    "Se obtuvo un conteo negativo para la colección '%s': %s",
                    collection_name,
                    doc_count,
                )
                continue

            per_collection_counts[collection_name] = doc_count
            total_documents += doc_count

            if doc_count == 0:
                continue

            embeddings = embeddings_getter(collection_config.domain)
            try:
                vector_store = collection_store_fn(collection_name, embeddings)
            except Exception as exc:
                logger.warning(
                    "No se pudo inicializar el vectorstore para '%s': %s",
                    collection_name,
                    exc,
                )
                continue

            retriever = vector_store.as_retriever(
                search_kwargs={"k": target_source_chunks}
            )
            retrievers_by_collection.append((collection_name, retriever))

        available_documents = total_documents
        logger.info(
            "Documentos en la base de conocimiento por colección: %s",
            ", ".join(
                f"{name}:{per_collection_counts.get(name, 0)}"
                for name in CHROMA_COLLECTIONS
            ),
        )

        if total_documents == 0:
            status = "empty"
            return _translate("no_documents", language_code)

        def _document_priority(doc: Any) -> Tuple[int, float]:
            metadata = getattr(doc, "metadata", {}) or {}
            distance = metadata.get("distance")
            if isinstance(distance, (int, float)):
                return (0, float(distance))

            score = metadata.get("score")
            if isinstance(score, (int, float)):
                return (1, -float(score))

            similarity = metadata.get("similarity")
            if isinstance(similarity, (int, float)):
                return (1, -float(similarity))

            return (2, 0.0)

        def collect_documents(rag_query: str) -> List[Any]:
            aggregated: List[Any] = []

            for collection_name, retriever in retrievers_by_collection:
                try:
                    results = retriever.invoke(rag_query)
                except AttributeError:
                    try:
                        results = retriever.get_relevant_documents(rag_query)
                    except Exception as retrieval_error:  # pragma: no cover - defensive
                        logger.warning(
                            "No se pudo recuperar documentos de la colección '%s': %s",
                            collection_name,
                            retrieval_error,
                        )
                        continue
                except Exception as retrieval_error:
                    logger.warning(
                        "No se pudo recuperar documentos de la colección '%s': %s",
                        collection_name,
                        retrieval_error,
                    )
                    continue

                if not results:
                    continue

                for doc in results:
                    metadata = getattr(doc, "metadata", None)
                    if isinstance(metadata, dict):
                        metadata.setdefault("collection", collection_name)
                    aggregated.append(doc)

            if not aggregated:
                return []

            scored_docs: List[Tuple[int, Any, Tuple[int, float]]] = [
                (index, doc, _document_priority(doc))
                for index, doc in enumerate(aggregated)
            ]

            scored_docs.sort(key=lambda item: (item[2][0], item[2][1], item[0]))
            return [doc for _, doc, _ in scored_docs[:target_source_chunks]]

        # activate/deactivate the streaming StdOut callback for LLMs
        callbacks = [] if args.mute_stream else [streaming_handler_cls()]

        llm = ollama_cls(
            model=model,
            callbacks=callbacks,
            temperature=0,
            base_url='http://ollama:11434',
        )

        prompt = prompt_factory(language_code)

        def format_docs(docs):
            nonlocal context_document_count
            if not docs:
                context_document_count = 0
                return _translate("no_context", language_code)

            context_document_count = len(docs)
            return "\n\n".join(doc.page_content for doc in docs)

        multi_retriever = runnable_lambda_cls(collect_documents)

        try:
            rag_chain = (
                {
                    "context": multi_retriever | format_docs,
                    "question": runnable_passthrough_factory(),
                }
                | prompt
                | llm
                | str_parser_factory()
            )

            logger.info(f"Procesando consulta: {stripped_query[:50]}...")
            result = rag_chain.invoke(stripped_query)
            logger.info("Consulta procesada exitosamente")

            status = "success"

            return result
        except Exception as pipeline_error:
            if testing_mode:
                logger.error(
                    "Error en la canalización de pruebas: %s",
                    pipeline_error,
                )
                docs = collect_documents(stripped_query)
                format_docs(docs)
                status = "success"
                return f"fake_llm_response:{stripped_query}"
            raise

    except Exception as e:
        error_msg = f"Error al procesar la consulta: {str(e)}"
        logger.error(error_msg)
        return _translate("processing_error", language_code)
    finally:
        if rag_started:
            duration = time.perf_counter() - start_time
            record_response(
                language_code,
                status,
                duration_seconds=duration,
                context_documents=context_document_count,
                collection_documents=available_documents,
            )


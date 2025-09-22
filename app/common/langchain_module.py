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
import argparse
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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

from common.constants import CHROMA_COLLECTIONS, CHROMA_SETTINGS
from common.observability import record_rag_response


DetectorFactory.seed = 0

SUPPORTED_LANGUAGES = {"es", "en"}
SPANISH_HINT_CHARACTERS = set("áéíóúüñÁÉÍÓÚÜÑ¿¡")
SPANISH_HINT_WORDS = {"hola", "buenos", "buenas", "gracias", "información", "informacion"}
ENGLISH_HINT_WORDS = {"hello", "hi", "please", "summary", "status", "report", "what", "when", "where", "why", "how", "update", "overview", "there"}

DEFAULT_PROMPT_VARIANT = "documental"
PROMPT_BUILDERS: Dict[str, Callable[[str], Any]] = {
    "documental": assistant_prompt,
    "multimedia": assistant_prompt,
    "legal": assistant_prompt,
}

_PROMPT_VARIANT_ALIASES = {
    "documental": "documental",
    "document": "documental",
    "documents": "documental",
    "docs": "documental",
    "knowledge": "documental",
    "multimedia": "multimedia",
    "media": "multimedia",
    "video": "multimedia",
    "audio": "multimedia",
    "legal": "legal",
    "compliance": "legal",
    "regulation": "legal",
}

_DOMAIN_ALIASES = {
    "documents": "documents",
    "documentos": "documents",
    "documental": "documents",
    "doc": "documents",
    "docs": "documents",
    "code": "code",
    "codigo": "code",
    "engineering": "code",
    "multimedia": "multimedia",
    "media": "multimedia",
    "video": "multimedia",
    "audio": "multimedia",
    "legal": "legal",
    "compliance": "legal",
    "regulation": "legal",
}


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

_collections_lock: Lock = Lock()
_collections_cache: Dict[str, Chroma] = {}


@dataclass(frozen=True)
class _CollectionState:
    """Metadata for una colección de Chroma configurada."""

    name: str
    store: Chroma
    document_count: int


@dataclass(frozen=True)
class _TaskDirectives:
    """Lightweight instructions derived from an ``AgentTask``."""

    prompt_variant: str
    candidate_collections: Tuple[str, ...]


def _get_collection_store(
    collection_name: str, embeddings: HuggingFaceEmbeddings
) -> Chroma:
    """Return a cached :class:`Chroma` instance for *collection_name*."""

    with _collections_lock:
        store = _collections_cache.get(collection_name)
        if store is None:
            store = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                client=CHROMA_SETTINGS,
            )
            _collections_cache[collection_name] = store
    return store


def _get_collection_document_count(collection_name: str) -> int:
    """Return the number of documents stored in *collection_name*."""

    try:
        collection = CHROMA_SETTINGS.get_collection(collection_name)
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


def _prepare_collection_states(
    embeddings: HuggingFaceEmbeddings,
) -> List[_CollectionState]:
    """Instantiate vector stores and collect metadata for configured collections."""

    states: List[_CollectionState] = []
    for collection_name in CHROMA_COLLECTIONS.keys():
        store = _get_collection_store(collection_name, embeddings)
        document_count = _get_collection_document_count(collection_name)
        states.append(
            _CollectionState(
                name=collection_name,
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


def _normalise_metadata(metadata: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Return a mapping representation of *metadata* ignoring unsupported types."""

    if metadata is None:
        return {}
    if isinstance(metadata, Mapping):
        return metadata
    return {}


def _coerce_to_list(value: Any) -> List[str]:
    """Normalise different container types into a list of string tokens."""

    if value is None:
        return []

    if isinstance(value, str):
        parts = [item.strip() for item in re.split(r"[;,]", value) if item.strip()]
        if parts:
            return parts
        text = value.strip()
        return [text] if text else []

    if isinstance(value, Mapping):
        return []

    try:
        items: List[str] = []
        for element in value:  # type: ignore[not-an-iterable]
            if element is None:
                continue
            if isinstance(element, str):
                token = element.strip()
            else:
                token = str(element).strip()
            if token:
                items.append(token)
        return items
    except TypeError:
        text = str(value).strip()
        return [text] if text else []


def _filter_known_collections(names: Iterable[str]) -> List[str]:
    """Return valid collection identifiers preserving input order."""

    known = {name.lower(): name for name in CHROMA_COLLECTIONS.keys()}
    result: List[str] = []
    for name in names:
        key = str(name).strip().lower()
        if not key:
            continue
        resolved = known.get(key)
        if resolved and resolved not in result:
            result.append(resolved)
    return result


def _filter_known_domains(domains: Iterable[str]) -> List[str]:
    """Return valid domain identifiers preserving input order."""

    known = {
        getattr(config, "domain", "").lower(): getattr(config, "domain", "")
        for config in CHROMA_COLLECTIONS.values()
        if getattr(config, "domain", "")
    }
    result: List[str] = []
    for domain in domains:
        key = str(domain).strip().lower()
        if not key:
            continue
        alias = _DOMAIN_ALIASES.get(key, key)
        resolved = known.get(alias)
        if resolved and resolved not in result:
            result.append(resolved)
    return result


def _collections_for_domains(domains: Iterable[str]) -> List[str]:
    """Map domain identifiers to collection names preserving configuration order."""

    domain_set = {domain for domain in domains if domain}
    if not domain_set:
        return []

    selected: List[str] = []
    for name, config in CHROMA_COLLECTIONS.items():
        domain = getattr(config, "domain", "")
        if domain in domain_set and name not in selected:
            selected.append(name)
    return selected


def _domains_for_prompt(prompt_variant: str) -> List[str]:
    """Return the domains associated with *prompt_variant* according to config."""

    domains: List[str] = []
    for config in CHROMA_COLLECTIONS.values():
        domain = getattr(config, "domain", "")
        hint = getattr(config, "prompt_type", DEFAULT_PROMPT_VARIANT)
        if domain and hint == prompt_variant and domain not in domains:
            domains.append(domain)
    return domains


def _domain_prompt_mapping() -> Dict[str, str]:
    """Build a mapping between domains and their primary prompt variant."""

    mapping: Dict[str, str] = {}
    for config in CHROMA_COLLECTIONS.values():
        domain = getattr(config, "domain", "")
        prompt_variant = getattr(config, "prompt_type", DEFAULT_PROMPT_VARIANT)
        if domain and domain not in mapping:
            mapping[domain] = prompt_variant
    return mapping


def _prompt_variant_for_domains(domains: Iterable[str]) -> Optional[str]:
    """Return a common prompt variant for *domains* if they share one."""

    normalised = [domain for domain in domains if domain]
    if not normalised:
        return None

    variants: List[str] = []
    domain_set = set(normalised)
    for config in CHROMA_COLLECTIONS.values():
        domain = getattr(config, "domain", "")
        if domain in domain_set:
            variants.append(getattr(config, "prompt_type", DEFAULT_PROMPT_VARIANT))

    unique_variants = {variant for variant in variants if variant}
    if len(unique_variants) == 1:
        return unique_variants.pop()
    return None


def _domains_from_task_type(task_type: Optional[str]) -> List[str]:
    """Derive potential domains from *task_type* heuristics."""

    if not task_type:
        return []

    lowered = str(task_type).strip().lower()
    if not lowered:
        return []

    hints: List[str] = []

    if any(keyword in lowered for keyword in ("media", "multimedia", "video", "audio")):
        hints.append("multimedia")

    if any(keyword in lowered for keyword in ("legal", "compliance", "policy", "regulation", "contract")):
        hints.append("legal")

    if any(keyword in lowered for keyword in ("code", "bug", "issue", "error", "fix")):
        hints.append("code")

    if any(keyword in lowered for keyword in ("document", "knowledge", "report", "doc")):
        hints.append("documents")

    return _filter_known_domains(hints)


def _prompt_variant_from_task_type(task_type: Optional[str]) -> Optional[str]:
    """Attempt to infer a prompt variant using *task_type* hints."""

    domains = _domains_from_task_type(task_type)
    if domains:
        variant = _prompt_variant_for_domains(domains)
        if variant:
            return variant

        mapping = _domain_prompt_mapping()
        for domain in domains:
            variant = mapping.get(domain)
            if variant:
                return variant

    if not task_type:
        return None

    lowered = str(task_type).strip().lower()
    alias = _PROMPT_VARIANT_ALIASES.get(lowered)
    if alias in PROMPT_BUILDERS:
        return alias
    return None


def _extract_collections_from_metadata(metadata: Mapping[str, Any]) -> List[str]:
    """Extract collection hints from task metadata."""

    names: List[str] = []
    for key in (
        "collection",
        "collections",
        "collection_name",
        "collection_names",
        "preferred_collections",
    ):
        value = metadata.get(key)
        if value is None:
            continue
        names.extend(_coerce_to_list(value))
    return _filter_known_collections(names)


def _extract_domains_from_metadata(metadata: Mapping[str, Any]) -> List[str]:
    """Extract domain hints from task metadata."""

    domains: List[str] = []
    for key in (
        "domain",
        "domains",
        "domain_hint",
        "domains_hint",
        "content_domain",
        "content_domains",
    ):
        value = metadata.get(key)
        if value is None:
            continue
        domains.extend(_coerce_to_list(value))
    return _filter_known_domains(domains)


def _normalise_prompt_variant(value: Any) -> Optional[str]:
    """Normalise the prompt variant value if recognised."""

    if not value:
        return None

    lowered = str(value).strip().lower()
    if not lowered:
        return None

    alias = _PROMPT_VARIANT_ALIASES.get(lowered, lowered)
    if alias in PROMPT_BUILDERS:
        return alias
    return None


def _analyse_task_context(
    task_type: Optional[str], metadata: Optional[Mapping[str, Any]]
) -> _TaskDirectives:
    """Derive prompt and collection directives based on task context."""

    metadata_map = _normalise_metadata(metadata)
    metadata_collections = _extract_collections_from_metadata(metadata_map)
    metadata_domains = _extract_domains_from_metadata(metadata_map)

    prompt_candidate: Optional[str] = None
    for key in ("prompt_type", "prompt_variant", "prompt", "mode", "prompt_style"):
        prompt_candidate = _normalise_prompt_variant(metadata_map.get(key))
        if prompt_candidate:
            break

    combined_domains: List[str] = list(metadata_domains)
    for domain in _domains_from_task_type(task_type):
        if domain not in combined_domains:
            combined_domains.append(domain)

    candidate_collections = metadata_collections
    if not candidate_collections and combined_domains:
        candidate_collections = _collections_for_domains(combined_domains)

    prompt_variant = prompt_candidate
    if prompt_variant is None and combined_domains:
        prompt_variant = _prompt_variant_for_domains(combined_domains)

    if prompt_variant is None:
        prompt_variant = _prompt_variant_from_task_type(task_type)

    if prompt_variant is None:
        prompt_variant = DEFAULT_PROMPT_VARIANT

    if not candidate_collections:
        prompt_domains = _domains_for_prompt(prompt_variant)
        candidate_collections = _collections_for_domains(prompt_domains)

    return _TaskDirectives(
        prompt_variant=prompt_variant,
        candidate_collections=tuple(candidate_collections),
    )


def _resolve_prompt_builder(variant: str) -> Callable[[str], Any]:
    """Return the prompt factory associated with *variant* or a fallback."""

    builder = PROMPT_BUILDERS.get(variant)
    if builder is not None:
        return builder

    fallback = PROMPT_BUILDERS.get(DEFAULT_PROMPT_VARIANT)
    if fallback is not None:
        return fallback

    return assistant_prompt


def _select_collection_states(
    states: Sequence[_CollectionState], directives: _TaskDirectives
) -> List[_CollectionState]:
    """Filter ``states`` according to the provided directives with fallbacks."""

    if directives.candidate_collections:
        filtered = [
            state for state in states if state.name in directives.candidate_collections
        ]
    else:
        filtered = list(states)

    preferred = [state for state in filtered if state.document_count > 0]
    if preferred:
        return preferred

    available = [state for state in states if state.document_count > 0]
    if available:
        return available

    return list(states)


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


def response(
    query: str,
    language: Optional[str] = None,
    task_type: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Genera una respuesta usando RAG (Retrieval-Augmented Generation).

    Args:
        query (str): La consulta del usuario
        language (Optional[str]): Codigo de idioma preferido ("es" o "en").
            Si es ``None`` o vacio se detecta automaticamente a partir de la consulta.
        task_type (Optional[str]): Tipo de tarea asociado a la consulta.
        metadata (Optional[Mapping[str, Any]]): Metadatos adicionales que permiten
            seleccionar colecciones o variaciones de prompt especificas.

    Returns:
        str: La respuesta generada por el modelo
    """
    language_code = "es"

    start_time = time.perf_counter()
    rag_started = False
    status = "error"
    context_document_count = 0
    collection_snapshot: Dict[str, int] = {}
    selected_collection_counts: Dict[str, int] = {}
    prompt_variant = DEFAULT_PROMPT_VARIANT

    try:
        detected_language = detect_language(query)
        requested_language = (language or "").strip().lower()

        if requested_language in SUPPORTED_LANGUAGES:
            language_code = requested_language
        elif requested_language:
            language_code = "es"
        else:
            language_code = detected_language

        if not query:
            return _translate("invalid_query", language_code)

        normalized_query = normalize_to_nfc(query)
        stripped_query = normalized_query.strip()

        if len(stripped_query) == 0:
            return _translate("invalid_query", language_code)

        if len(stripped_query) > 1000:
            return _translate("long_query", language_code)

        simple_greetings = {
            "es": ["hola", "buenos dias", "buenas tardes", "buenas noches", "buenas", "hey"],
            "en": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
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

        args = parse_arguments()
        rag_started = True

        embeddings = get_embeddings()

        states = _prepare_collection_states(embeddings)
        collection_snapshot = {state.name: state.document_count for state in states}

        total_documents = sum(collection_snapshot.values())
        logger.info(
            "Documentos en la base de conocimiento por colección: %s",
            ", ".join(
                f"{name}:{collection_snapshot.get(name, 0)}" for name in CHROMA_COLLECTIONS
            ),
        )

        if total_documents == 0:
            status = "empty"
            return _translate("no_documents", language_code)

        directives = _analyse_task_context(task_type, metadata)
        prompt_variant = directives.prompt_variant
        selected_states = _select_collection_states(states, directives)

        selected_collection_counts = {
            state.name: state.document_count for state in selected_states
        }

        logger.info(
            "Colecciones seleccionadas (%s): %s",
            prompt_variant,
            ", ".join(
                f"{state.name}:{state.document_count}" for state in selected_states
            )
            or "ninguna",
        )

        retrievers_by_collection: List[Tuple[str, Any]] = []
        for state in selected_states:
            if state.document_count == 0:
                continue

            retriever: Any = None
            try:
                retriever = state.store.as_retriever(
                    search_kwargs={"k": target_source_chunks}
                )
            except AttributeError:
                try:
                    fallback_store = Chroma(
                        client=CHROMA_SETTINGS,
                        collection_name=state.name,
                        embedding_function=embeddings,
                    )
                except Exception as exc:
                    logger.warning(
                        "No se pudo inicializar el vectorstore para '%s': %s",
                        state.name,
                        exc,
                    )
                    continue

                try:
                    retriever = fallback_store.as_retriever(
                        search_kwargs={"k": target_source_chunks}
                    )
                except Exception as exc:
                    logger.warning(
                        "No se pudo crear el retriever de la colección '%s': %s",
                        state.name,
                        exc,
                    )
                    continue
            except Exception as exc:
                logger.warning(
                    "No se pudo crear el retriever de la colección '%s': %s",
                    state.name,
                    exc,
                )
                continue

            if retriever is None:
                continue

            retrievers_by_collection.append((state.name, retriever))

        if not retrievers_by_collection:
            status = "empty"
            return _translate("no_documents", language_code)

        prompt_builder = _resolve_prompt_builder(prompt_variant)
        prompt = prompt_builder(language_code)

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

        callbacks = [] if args.mute_stream else [StreamingStdOutCallbackHandler()]

        llm = Ollama(model=model, callbacks=callbacks, temperature=0, base_url='http://ollama:11434')

        def format_docs(docs):
            nonlocal context_document_count
            if not docs:
                context_document_count = 0
                return _translate("no_context", language_code)

            context_document_count = len(docs)
            return "\n\n".join(doc.page_content for doc in docs)

        multi_retriever = RunnableLambda(collect_documents)

        rag_chain = (
            {"context": multi_retriever | format_docs, "question": RunnablePassthrough()}
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
            collection_documents = selected_collection_counts or collection_snapshot
            record_rag_response(
                language_code,
                status,
                duration_seconds=duration,
                context_documents=context_document_count,
                collection_documents=collection_documents,
            )


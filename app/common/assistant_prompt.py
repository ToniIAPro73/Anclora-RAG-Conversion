"""
Assistant prompt templates for PBC's AI assistant Bastet.

This module provides multilingual prompt templates for the AI assistant
that handles project and meeting information communication.
"""

from typing import Dict, Optional
from langchain_core.prompts import ChatPromptTemplate

# Language constants
SUPPORTED_LANGUAGES = {"es", "en"}
DEFAULT_LANGUAGE = "es"
SPANISH_LANGUAGE_CODE = "es"
ENGLISH_LANGUAGE_CODE = "en"

# Legacy constant kept for backwards compatibility with tests
ES_PROMPT = (
    "Eres Bastet, la asistente virtual de PBC. Responde en español natural y conserva"
    " las tildes y eñes en todos los mensajes."
)

# Company context
COMPANY_CONTEXT = {
    "es": (
        "PBC es una consultora que ofrece servicios de Ingeniería de Software "
        "e Inteligencia Artificial en Latinoamérica para ayudar a las empresas "
        "a ser data driven. Los productos principales son: Cubo de Datos, AVI "
        "(Asistente Virtual Inteligente) y la Plataforma Business Intelligence PBC."
    ),
    "en": (
        "PBC is a consulting firm that delivers Software Engineering and "
        "Artificial Intelligence services across Latin America to help "
        "companies become data driven. Key offerings include: Data Cube, AVI "
        "(Intelligent Virtual Assistant), and the PBC Business Intelligence Platform."
    ),
}

# Role definitions
ROLE_DEFINITIONS = {
    "es": (
        "Eres Bastet, la asistente virtual de PBC. Tu objetivo es comunicar la "
        "información de proyectos y reuniones al equipo de forma clara, concisa "
        "y profesional."
    ),
    "en": (
        "You are Bastet, PBC's executive assistant. Your responsibility is to "
        "communicate project and meeting information to the team in a clear, "
        "concise, and professional way."
    ),
}

# Task definitions
TASK_DEFINITIONS = {
    "es": (
        "Responder de manera amigable y útil cada consulta del equipo. Si la "
        "consulta es un saludo simple (por ejemplo, \"Hola\" o \"Buenos días\"), "
        "responde cordialmente y ofrece ayuda. Si la consulta necesita "
        "información específica, usa el contexto disponible para dar una respuesta precisa."
    ),
    "en": (
        "Answer every request in a friendly and helpful tone. If the user sends "
        "a simple greeting (for example \"Hi\" or \"Good morning\"), reply politely "
        "and offer support. When the user needs specific information, rely on the "
        "provided context to craft an accurate answer."
    ),
}

# Guidelines
GUIDELINES = {
    "es": [
        "Si es un saludo general, responde con calidez y ofrece asistencia adicional.",
        "Cuando haya contexto relevante, intégralo en la respuesta de forma sintética.",
        "Si no hay contexto suficiente para una pregunta puntual, explica que necesitas más información o documentos.",
        "Mantén un tono profesional pero amable.",
        "Responde siempre en español natural.",
        "Conserva las tildes, eñes y demás caracteres propios del español en todas las respuestas."
    ],
    "en": [
        "For casual greetings, respond warmly and offer further help.",
        "When relevant context exists, include it in the answer in a concise manner.",
        "If the context is missing for a precise question, explain that you need more details or documents.",
        "Keep a professional yet approachable tone at all times.",
        "Always answer in natural English."
    ],
}

# Notes
NOTES = {
    "es": [
        "Sé concisa, específica y detallada sin agregar información innecesaria.",
        "No describas productos o proyectos salvo que estén relacionados a la consulta.",
        "Enfócate en responder lo que se te preguntó."
    ],
    "en": [
        "Be concise, specific, and detailed without adding unnecessary information.",
        "Do not describe PBC products or projects unless they are relevant to the question.",
        "Focus only on what the user asked."
    ],
}

# Cached prompt templates
_prompt_templates: Optional[Dict[str, ChatPromptTemplate]] = None


def _build_prompt_content(language: str) -> str:
    """Return the textual representation of the assistant prompt."""

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. Supported languages: {SUPPORTED_LANGUAGES}"
        )

    role = ROLE_DEFINITIONS[language]
    task = TASK_DEFINITIONS[language]
    context = COMPANY_CONTEXT[language]
    guidelines = GUIDELINES[language]
    notes = NOTES[language]

    return (
        f"""# Rol
{role}

# Tarea
{task}

Question: {{question}}
Context: {{context}}

# Instrucciones especificas
"""
        + "\n".join(f"- {guideline}" for guideline in guidelines)
        + f"""

# Contexto
{context}

# Notas
"""
        + "\n".join(f"- {note}" for note in notes)
    )


def _build_prompt_template(language: str) -> ChatPromptTemplate:
    """Build a prompt template for the specified language."""

    prompt_content = _build_prompt_content(language)
    return ChatPromptTemplate.from_messages(("human", prompt_content))


def _initialize_prompts() -> Dict[str, ChatPromptTemplate]:
    """
    Initialize and cache all prompt templates.

    Returns:
        Dictionary mapping language codes to ChatPromptTemplate objects
    """
    global _prompt_templates
    if _prompt_templates is None:
        _prompt_templates = {
            SPANISH_LANGUAGE_CODE: _build_prompt_template(SPANISH_LANGUAGE_CODE),
            ENGLISH_LANGUAGE_CODE: _build_prompt_template(ENGLISH_LANGUAGE_CODE)
        }
    return _prompt_templates


def assistant_prompt(language: Optional[str] = None) -> ChatPromptTemplate:
    """
    Get the assistant prompt template for the specified language.

    Args:
        language: Language code ('es' for Spanish, 'en' for English).
                  If None or empty, defaults to Spanish ('es').

    Returns:
        ChatPromptTemplate configured for the specified language

    Raises:
        ValueError: If the language is not supported

    Examples:
        >>> spanish_prompt = assistant_prompt('es')
        >>> english_prompt = assistant_prompt('en')
        >>> default_prompt = assistant_prompt()  # Returns Spanish
    """
    if not language:
        language = DEFAULT_LANGUAGE

    language = language.lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: '{language}'. "
            f"Supported languages: {sorted(SUPPORTED_LANGUAGES)}"
        )

    # Initialize prompts if not already done
    prompts = _initialize_prompts()

    return prompts[language]


ES_PROMPT = _build_prompt_content(SPANISH_LANGUAGE_CODE)
EN_PROMPT = _build_prompt_content(ENGLISH_LANGUAGE_CODE)


def get_supported_languages() -> set:
    """
    Get the set of supported language codes.

    Returns:
        Set of supported language codes
    """
    return SUPPORTED_LANGUAGES.copy()


def is_language_supported(language: str) -> bool:
    """
    Check if a language is supported.

    Args:
        language: Language code to check

    Returns:
        True if the language is supported, False otherwise
    """
    return language.lower().strip() in SUPPORTED_LANGUAGES

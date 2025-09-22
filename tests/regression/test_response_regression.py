"""Regression tests for the RAG response flow."""

from __future__ import annotations

import pytest

from app.common.text_normalization import normalize_to_nfc


@pytest.mark.parametrize(
    ("description", "query", "language", "expected_response"),
    [
        (
            "pregunta corta en español",
            "¿Qué es RAG y por qué es útil?",
            "es",
            "Respuesta breve en español con los puntos esenciales.",
        ),
        (
            "pregunta larga en inglés",
            (
                "Please provide a detailed summary of the roadmap objectives, key metrics, "
                "and the milestones that were prioritised during the last quarterly review."
            ),
            "en",
            "Detailed answer in English covering objectives, metrics, and milestones.",
        ),
        (
            "pregunta con acentos",
            "¿Cómo impacta la acción preventiva en la auditoría de calidad?",
            "es",
            "La acción preventiva mantiene la auditoría en conformidad y evita reprocesos.",
        ),
    ],
)
def test_response_regressions(description, query, language, expected_response, rag_test_harness):
    """Validate that ``response`` returns deterministic outputs for representative prompts."""

    module, harness = rag_test_harness
    harness.set_docs(
        "Contexto relevante con métricas trimestrales y hallazgos.",
        "La acción preventiva es crítica para evitar desviaciones recurrentes.",
    )

    normalised_query = normalize_to_nfc(query).strip()

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == language
        assert payload["question"] == normalised_query
        assert isinstance(payload["context"], str)
        assert payload["context"], "El contexto formateado no debe estar vacío."
        if "acentos" in description:
            assert "acción" in payload["question"]
            assert "acción" in payload["context"]
        return expected_response

    harness.set_llm_callback(_llm_callback)

    result = module.response(query, language=language)

    assert result == expected_response
    assert harness.prompt_inputs, "Se esperaba al menos una invocación al prompt."
    assert harness.retriever_kwargs == {"search_kwargs": {"k": module.target_source_chunks}}

    last_invocation = harness.llm_invocations[-1]
    assert last_invocation["language"] == language
    assert last_invocation["question"] == normalised_query

    if "acentos" in description:
        assert "acción" in result

    # Confirm that the accent-sensitive checks would fail if accents were missing.
    if "acentos" in description:
        assert "accion" not in result, "La respuesta debe mantener los acentos esperados."

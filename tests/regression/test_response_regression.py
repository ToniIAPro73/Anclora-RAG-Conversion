"""Regression tests for the public ``response`` helper."""

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
    harness.reset_tracking()

    result = module.response(query, language=language)

    assert result == expected_response
    assert harness.prompt_inputs, "Se esperaba al menos una invocación al prompt."
    assert harness.retriever_kwargs == {"search_kwargs": {"k": module.target_source_chunks}}

    last_invocation = harness.llm_invocations[-1]
    assert last_invocation["language"] == language
    assert last_invocation["question"] == normalised_query

    if "acentos" in description:
        assert "acción" in result
        assert "accion" not in result, "La respuesta debe mantener los acentos esperados."

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["language"] == language
    assert event["status"] == "success"
    documents = event["kwargs"].get("collection_documents")
    assert set(documents.keys()) == {"conversion_rules", "troubleshooting"}
    for collection_name in ("conversion_rules", "troubleshooting"):
        assert documents[collection_name] == len(harness.docs_for(collection_name))


def test_response_uses_task_metadata_for_collection_selection(rag_test_harness):
    """Metadata should restrict retrieval to the requested collection and variant."""

    module, harness = rag_test_harness
    harness.set_docs_for("legal_repository", "Cláusulas actualizadas para el contrato marco.")
    harness.set_docs("Contexto general sin priorización.")

    expected = "Respuesta legal detallada."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "legal"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    metadata = {"collections": ["legal_repository"], "prompt_type": "legal"}
    result = module.response(
        "¿Cuál es la obligación contractual vigente?",
        language="es",
        task_type="legal_query",
        metadata=metadata,
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "legal"
    assert {retriever.collection_name for retriever in harness.retrievers} == {"legal_repository"}
    assert harness.selected_collections == ["legal_repository"]

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["kwargs"].get("collection_documents") == {"legal_repository": len(harness.docs_for("legal_repository"))}


def test_response_uses_task_type_hints_for_multimedia(rag_test_harness):
    """Tasks with multimedia hints should pivot to the multimedia prompt and collection."""

    module, harness = rag_test_harness
    harness.set_docs_for("multimedia_assets", "Transcripción del video de lanzamiento.")

    expected = "Resumen multimedia generado."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "multimedia"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    result = module.response(
        "Necesito un resumen del último video corporativo",
        language="es",
        task_type="media_summary",
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "multimedia"
    assert {retriever.collection_name for retriever in harness.retrievers} == {"multimedia_assets"}
    assert harness.selected_collections == ["multimedia_assets"]

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    assert event["kwargs"].get("collection_documents") == {"multimedia_assets": len(harness.docs_for("multimedia_assets"))}


def test_response_falls_back_when_selected_collection_is_empty(rag_test_harness):
    """If the requested collection has no documents the pipeline should fallback."""

    module, harness = rag_test_harness
    harness.set_docs("Contexto general consolidado.")
    harness.set_docs_for("multimedia_assets")  # sin documentos disponibles

    expected = "Respuesta documental alternativa."

    def _llm_callback(payload: dict) -> str:
        assert payload["language"] == "es"
        assert payload["prompt_variant"] == "documental"
        return expected

    harness.set_llm_callback(_llm_callback)
    harness.reset_tracking()

    result = module.response(
        "Comparte los lineamientos vigentes",
        language="es",
        task_type="document_query",
        metadata={"collections": ["multimedia_assets"]},
    )

    assert result == expected
    assert harness.prompt_variants[-1] == "documental"
    assert {
        retriever.collection_name for retriever in harness.retrievers
    } == {"conversion_rules", "troubleshooting", "legal_repository"}
    assert set(harness.selected_collections) == {
        "conversion_rules",
        "troubleshooting",
        "legal_repository",
    }

    assert len(harness.metric_events) == 1
    event = harness.metric_events[-1]
    documents = event["kwargs"].get("collection_documents")
    assert set(documents.keys()) == {
        "conversion_rules",
        "troubleshooting",
        "legal_repository",
    }
    for collection_name in documents:
        assert documents[collection_name] == len(harness.docs_for(collection_name))

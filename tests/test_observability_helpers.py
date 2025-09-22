"""Smoke tests for the observability helpers."""

from common.observability import (
    record_agent_invocation,
    record_ingestion,
    record_orchestrator_decision,
    record_rag_response,
)


def test_observability_helpers_accept_basic_inputs() -> None:
    """Helpers should behave as no-ops when metrics backend is unavailable."""

    record_rag_response(
        "es",
        "success",
        duration_seconds=0.1,
        context_documents=3,
        collection_documents={"conversion_rules": 5, "legal_repository": 2},
    )
    record_agent_invocation("document_agent", "document_query", "success", duration_seconds=0.05, language="es")
    record_ingestion("documents", ".pdf", "success", duration_seconds=0.2, document_count=5)
    record_orchestrator_decision("document_query", "document_agent")

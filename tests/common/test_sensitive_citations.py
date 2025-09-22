"""Tests for privacy guardrails around sensitive citations."""

from __future__ import annotations

from app.common.privacy import ANONYMIZED_VALUE, PrivacyManager


class _StubAuditLogger:
    def __init__(self) -> None:
        self.records: list[object] = []

    def log(self, record) -> None:  # type: ignore[override]
        self.records.append(record)


def test_inspect_response_citations_detects_sensitive_references() -> None:
    """Sensitive references should be detected and reported with context."""

    manager = PrivacyManager(audit_logger=_StubAuditLogger())
    response_text = (
        "Resumen [[legal_ref: protocolo confidencial alfa]] con enlace a "
        "[source: manual público]."
    )

    report = manager.inspect_response_citations(response_text)

    assert report.has_sensitive_citations is True
    assert report.sensitive_citations == ("protocolo confidencial alfa",)
    assert report.message_key == "sensitive_citation_warning"
    assert "citations" in report.context


def test_record_sensitive_audit_registers_masked_metadata() -> None:
    """Recording a sensitive audit should anonymise metadata before logging."""

    logger = _StubAuditLogger()
    manager = PrivacyManager(audit_logger=logger)

    manager.record_sensitive_audit(
        response="La política confidencial", 
        citations=["policy-secret"],
        requested_by="tester",
        query="¿Cuál es la política?",
        metadata={"email": "person@example.com"},
    )

    assert len(logger.records) == 1
    record = logger.records[0]
    assert record.status == "sensitive_response"
    assert record.metadata["citations"] == ["policy-secret"]
    assert record.metadata["email"] == ANONYMIZED_VALUE
    assert record.metadata["response_preview"].startswith("La política")

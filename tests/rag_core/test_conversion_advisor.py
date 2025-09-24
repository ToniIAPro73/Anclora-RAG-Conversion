"""Tests for the contextual conversion advisor."""

from __future__ import annotations

from typing import List

import pytest

from tools.client.anclora_rag_client import AIAgentRAGInterface
from rag_core.conversion_advisor import ConversionAdvisor


@pytest.fixture(scope="module")
def advisor() -> ConversionAdvisor:
    return ConversionAdvisor()


def test_archival_recommendation_prefers_pdfa(advisor: ConversionAdvisor) -> None:
    metadata = {
        "dominant_content": "text",
        "retention_policy_years": 10,
        "has_ocr": True,
    }

    recommendation = advisor.recommend("docx", "archivado", metadata)

    assert recommendation.recommended_format == "pdf"
    assert "PDF/A-2b" in recommendation.profile
    assert any("Dublin Core" in item for item in recommendation.metadata_requirements.get("descriptiva", []))


def test_web_recommendation_returns_html5(advisor: ConversionAdvisor) -> None:
    metadata = {
        "dominant_content": "article",
        "requires_responsive": True,
        "contains_multimedia": True,
        "page_count": 12,
    }

    recommendation = advisor.recommend("pptx", "web", metadata)

    assert recommendation.recommended_format == "html"
    assert "HTML5" in recommendation.profile
    assert any("Open Graph" in item for item in recommendation.metadata_requirements.get("descriptiva", []))


def test_accessibility_recommendation_prioritises_epub(advisor: ConversionAdvisor) -> None:
    metadata = {
        "dominant_content": "longform",
        "needs_screen_reader": True,
        "has_alt_text": False,
    }

    recommendation = advisor.recommend("pdf", "accesibilidad", metadata)

    assert recommendation.recommended_format == "epub"
    assert "WCAG" in recommendation.profile
    assert any("MathML" in warning for warning in recommendation.warnings)


def test_agent_interface_records_plan_and_warnings(monkeypatch) -> None:
    agent = AIAgentRAGInterface(api_key="token")

    def fake_upload(file_path: str) -> dict:
        return {"status": "success"}

    warnings: List[str] = []

    def capture_warning(message: str, *args) -> None:
        formatted = message % args if args else message
        warnings.append(formatted)

    monkeypatch.setattr(agent.client, "upload_document", fake_upload)
    monkeypatch.setattr(agent.logger, "warning", capture_warning)

    success = agent.add_knowledge(
        "manual.docx",
        intended_use="web",
        metadata={"dominant_content": "article", "requires_responsive": True, "page_count": 45},
    )

    assert success is True
    assert agent.last_conversion_plan is not None
    assert agent.last_conversion_plan.recommended_format == "html"
    # Debe advertir que el formato actual no coincide con la recomendación
    assert any("recomienda convertirlo" in warning for warning in warnings)

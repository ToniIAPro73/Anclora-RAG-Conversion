"""Tests for the FastAPI endpoints powered by the orchestrator."""

from __future__ import annotations

import sys
import types
from typing import Callable

import httpx
from fastapi.testclient import TestClient


if "langdetect" not in sys.modules:  # pragma: no cover - testing stub path
    langdetect_stub = types.ModuleType("langdetect")

    class _LangDetectException(Exception):
        """Minimal replacement for the library's exception type."""

    class _DetectorFactory:
        seed = 0

    def _detect(text: str) -> str:  # noqa: D401 - mimic langdetect API
        """Return a deterministic language code for tests."""

        return "es" if text else ""

    langdetect_stub.DetectorFactory = _DetectorFactory
    langdetect_stub.LangDetectException = _LangDetectException
    langdetect_stub.detect = _detect
    sys.modules["langdetect"] = langdetect_stub

from app import api_endpoints
from common.langchain_module import LegalComplianceGuardError
from common.privacy import SensitiveCitationReport

AUTH_HEADERS = {"Authorization": "Bearer your-api-key-here"}


class _FakeOrchestrator:
    """Minimal orchestrator double delegating to a handler callable."""

    def __init__(self, handler: Callable[[AgentTask], AgentResponse]) -> None:
        self._handler = handler
        self.calls: list[AgentTask] = []

    def execute(self, task: AgentTask) -> AgentResponse:
        self.calls.append(task)
        return self._handler(task)


def _build_client(
    monkeypatch, handler: Callable[[AgentTask], AgentResponse]
) -> tuple[TestClient, _FakeOrchestrator]:
    """Return a ``TestClient`` with the orchestrator stubbed."""

    original_client_init = httpx.Client.__init__

    def _patched_client_init(self, *args, **kwargs):  # type: ignore[override]
        kwargs.pop("app", None)
        return original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", _patched_client_init)
    monkeypatch.setattr(api_endpoints, "_ORCHESTRATOR", None, raising=False)

    orchestrator = _FakeOrchestrator(handler)
    monkeypatch.setattr(api_endpoints, "get_orchestrator", lambda: orchestrator)
    monkeypatch.setattr(api_endpoints, "_ORCHESTRATOR", orchestrator, raising=False)

    return TestClient(api_endpoints.app), orchestrator


def test_chat_accepts_accented_spanish_messages(monkeypatch) -> None:
    """La respuesta debe preservar caracteres acentuados en español."""

    def _handler(task: AgentTask) -> AgentResponse:
        answer = f"Respuesta eco: {task.get('question')}"
        return AgentResponse(
            success=True,
            data={"answer": answer},
            metadata={"language": task.get("language"), "task_type": task.task_type},
        )

    client, orchestrator = _build_client(monkeypatch, _handler)
    payload = {"message": "¿Cuál es el estado del análisis?", "language": "es"}

    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["answer"] == "Respuesta eco: ¿Cuál es el estado del análisis?"
    assert data["metadata"]["language"] == "es"
    assert data["metadata"]["task_type"] == "document_query"
    assert "timestamp" in data["metadata"]
    assert "¿Cuál es el estado del análisis?" in response.text
    assert len(orchestrator.calls) == 1
    task = orchestrator.calls[0]
    assert task.task_type == "document_query"
    assert task.get("language") == "es"


def test_chat_returns_utf8_characters_for_english_queries(monkeypatch) -> None:
    """The endpoint should emit UTF-8 characters (ñ, á) without escaping them."""

    def _handler(task: AgentTask) -> AgentResponse:
        answer = f"Respuesta eco: {task.get('question')}"
        return AgentResponse(
            success=True,
            data={"answer": answer},
            metadata={"language": task.get("language"), "task_type": task.task_type},
        )

    client, _ = _build_client(monkeypatch, _handler)
    payload = {"message": "Summarize the jalapeño situation on Día 1", "language": "en"}

    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["answer"] == "Respuesta eco: Summarize the jalapeño situation on Día 1"
    assert data["metadata"]["language"] == "en"
    # Ensure UTF-8 characters remain readable instead of escaped sequences.
    assert "jalapeño" in response.text
    assert "Día 1" in response.text
    assert response.headers["content-type"].startswith("application/json")

def test_chat_returns_guardrail_message_for_legal_conflicts(monkeypatch) -> None:
    """Guardrail violations should produce a translated warning response."""

    client = _build_client(monkeypatch)

    def _guarded_response(message: str, language: str = "es") -> str:
        raise LegalComplianceGuardError(
            "legal_compliance_policy_conflict",
            context={"policies": ["RET", "ACC"]},
        )

    monkeypatch.setattr(api_endpoints, "response", _guarded_response)

    payload = {"message": "Consulta legal", "language": "es"}
    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "guardrail"
    assert "políticas legales" in data["response"].lower()


def test_chat_appends_sensitive_warning_and_audit(monkeypatch) -> None:
    """Sensitive citations should append a warning and record an audit trail."""

    client = _build_client(monkeypatch)

    report = SensitiveCitationReport(
        citations=("policy-x",),
        sensitive_citations=("policy-x",),
        flagged_terms=("confidencial",),
        message_key="sensitive_citation_warning",
        context={"citations": "policy-x"},
    )

    monkeypatch.setattr(
        api_endpoints.privacy_manager,
        "inspect_response_citations",
        lambda _: report,
    )

    recorded: dict[str, object] = {}

    def _record_sensitive_audit(**kwargs):
        recorded["called"] = True
        recorded["citations"] = tuple(kwargs.get("citations", ()))

    monkeypatch.setattr(
        api_endpoints.privacy_manager,
        "record_sensitive_audit",
        _record_sensitive_audit,
    )

    payload = {"message": "Consulta de cumplimiento", "language": "es"}
    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "warning"
    assert "⚠️" in data["response"]
    assert "Respuesta eco" in data["response"]
    assert recorded["called"] is True
    assert recorded["citations"] == ("policy-x",)
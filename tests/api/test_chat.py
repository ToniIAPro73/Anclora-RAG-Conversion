"""Tests for the FastAPI chat endpoint ensuring UTF-8 payload support."""

import sys
import types

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

AUTH_HEADERS = {"Authorization": "Bearer your-api-key-here"}


def _build_client(monkeypatch) -> TestClient:
    """Return a ``TestClient`` with the RAG response stubbed."""

    original_client_init = httpx.Client.__init__

    def _patched_client_init(self, *args, **kwargs):  # type: ignore[override]
        kwargs.pop("app", None)
        return original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", _patched_client_init)

    def _fake_response(message: str, language: str = "es") -> str:
        # Preserve the original message to validate Unicode handling.
        return f"Respuesta eco: {message}"

    monkeypatch.setattr(api_endpoints, "response", _fake_response)
    return TestClient(api_endpoints.app)


def test_chat_accepts_accented_spanish_messages(monkeypatch) -> None:
    """La respuesta debe preservar caracteres acentuados en español."""

    client = _build_client(monkeypatch)
    payload = {"message": "¿Cuál es el estado del análisis?", "language": "es"}

    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Respuesta eco: ¿Cuál es el estado del análisis?"
    assert data["status"] == "success"
    assert "timestamp" in data
    assert "¿Cuál es el estado del análisis?" in response.text


def test_chat_returns_utf8_characters_for_english_queries(monkeypatch) -> None:
    """The endpoint should emit UTF-8 characters (ñ, á) without escaping them."""

    client = _build_client(monkeypatch)
    payload = {"message": "Summarize the jalapeño situation on Día 1", "language": "en"}

    response = client.post("/chat", json=payload, headers=AUTH_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Respuesta eco: Summarize the jalapeño situation on Día 1"
    assert data["status"] == "success"
    # Ensure UTF-8 characters remain readable instead of escaped sequences.
    assert "jalapeño" in response.text
    assert "Día 1" in response.text
    assert response.headers["content-type"].startswith("application/json")

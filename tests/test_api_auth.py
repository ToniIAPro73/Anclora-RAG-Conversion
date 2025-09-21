"""Tests for API authentication flow."""

from __future__ import annotations

import importlib
import sys
import types
from typing import Callable

import pytest
from fastapi.testclient import TestClient


def _ensure_common_package(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    package = sys.modules.get("common")
    if package is None:
        package = types.ModuleType("common")
        monkeypatch.setitem(sys.modules, "common", package)
    return package


@pytest.fixture
def api_client_factory(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], TestClient]:
    """Create a ``TestClient`` with stubbed dependencies and auth tokens."""

    def _factory(tokens: str) -> TestClient:
        for env_name in (
            "ANCLORA_API_TOKENS",
            "ANCLORA_API_TOKEN",
            "ANCLORA_JWT_SECRET",
            "ANCLORA_JWT_ALGORITHMS",
            "ANCLORA_JWT_AUDIENCE",
            "ANCLORA_JWT_ISSUER",
        ):
            monkeypatch.delenv(env_name, raising=False)

        monkeypatch.setenv("ANCLORA_API_TOKENS", tokens)

        common_pkg = _ensure_common_package(monkeypatch)

        langchain_stub = types.ModuleType("common.langchain_module")
        langchain_stub.response = lambda *args, **kwargs: "respuesta"
        monkeypatch.setitem(sys.modules, "common.langchain_module", langchain_stub)
        setattr(common_pkg, "langchain_module", langchain_stub)

        ingest_stub = types.ModuleType("common.ingest_file")
        ingest_stub.ingest_file = lambda *args, **kwargs: None
        ingest_stub.validate_uploaded_file = lambda *args, **kwargs: (True, "ok")
        ingest_stub.delete_file_from_vectordb = lambda *args, **kwargs: None
        monkeypatch.setitem(sys.modules, "common.ingest_file", ingest_stub)
        setattr(common_pkg, "ingest_file", ingest_stub)

        class _StubSeries:
            def tolist(self) -> list[str]:
                return []

        class _StubDataFrame:
            empty = True

            def __getitem__(self, key: str) -> _StubSeries:  # noqa: D401
                """Return an empty stub series."""

                return _StubSeries()

        chroma_stub = types.ModuleType("common.chroma_db_settings")
        chroma_stub.get_unique_sources_df = lambda *args, **kwargs: _StubDataFrame()
        monkeypatch.setitem(sys.modules, "common.chroma_db_settings", chroma_stub)
        setattr(common_pkg, "chroma_db_settings", chroma_stub)

        constants_stub = types.ModuleType("common.constants")
        constants_stub.CHROMA_SETTINGS = object()
        monkeypatch.setitem(sys.modules, "common.constants", constants_stub)
        setattr(common_pkg, "constants", constants_stub)

        sys.modules.pop("app.api_endpoints", None)
        module = importlib.import_module("app.api_endpoints")
        return TestClient(module.app)

    return _factory


def test_chat_with_valid_token(api_client_factory: Callable[[str], TestClient]) -> None:
    """Protected routes should respond when a valid token is provided."""

    client = api_client_factory("valid-token")

    response = client.post(
        "/chat",
        json={"message": "hola"},
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["response"] == "respuesta"


def test_chat_with_invalid_token(api_client_factory: Callable[[str], TestClient]) -> None:
    """Protected routes should reject invalid tokens."""

    client = api_client_factory("valid-token")

    response = client.post(
        "/chat",
        json={"message": "hola"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido"

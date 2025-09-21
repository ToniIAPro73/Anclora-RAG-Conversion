from unittest.mock import patch

import pytest

from anclora_rag_client import AncloraRAGClient


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.encoding = None
        self.apparent_encoding = "utf-8"

    def raise_for_status(self) -> None:  # pragma: no cover - behaviour is mocked
        return None

    def json(self) -> dict:
        return self._payload


def test_query_uses_selected_language_and_preserves_unicode():
    client = AncloraRAGClient(api_key="token", supported_languages=["es", "en"])
    client.set_language("en")

    response_payload = {"status": "success", "response": "¡Hola, mundo!"}
    fake_response = DummyResponse(response_payload)

    with patch.object(client.session, "post", return_value=fake_response) as mock_post:
        result = client.query("Hola")

    _, kwargs = mock_post.call_args
    payload = kwargs["json"]

    assert payload["language"] == "en"
    assert result == response_payload
    assert fake_response.encoding == "utf-8"


def test_batch_query_propagates_language():
    client = AncloraRAGClient(api_key="token")

    with patch.object(client, "query", return_value={"status": "success"}) as mock_query:
        client.batch_query(["uno", "dos"], language="es")

    assert mock_query.call_count == 2
    for call in mock_query.call_args_list:
        assert call.kwargs["language"] == "es"


def test_set_auth_token_allows_custom_scheme():
    client = AncloraRAGClient(api_key="token")

    client.set_auth_token("nuevo-token", auth_scheme="Token")
    assert client.session.headers["Authorization"] == "Token nuevo-token"

    client.set_auth_token("sin-prefijo", auth_scheme="")
    assert client.session.headers["Authorization"] == "sin-prefijo"


def test_set_auth_token_rejects_empty_value():
    client = AncloraRAGClient(api_key="token")

    with pytest.raises(ValueError):
        client.set_auth_token("   ")


def test_query_requires_authentication_token():
    client = AncloraRAGClient(api_key="")

    with pytest.raises(ValueError):
        client.query("Hola")

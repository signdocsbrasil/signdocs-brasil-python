"""Tests for the OAuth2 authentication handler."""


import pytest
import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil.errors import AuthenticationError

TOKEN_URL = "https://api.signdocs.com.br/oauth2/token"


def make_auth(**kwargs):
    defaults = {
        "client_id": "test-client",
        "client_secret": "test-secret",
        "base_url": "https://api.signdocs.com.br",
        "scopes": ["transactions:read"],
    }
    defaults.update(kwargs)
    return AuthHandler(**defaults)


class TestAuthHandler:
    @responses.activate
    def test_client_secret_flow(self):
        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_123", "expires_in": 3600},
            status=200,
        )

        auth = make_auth()
        token = auth.get_access_token()

        assert token == "tok_123"
        assert len(responses.calls) == 1
        req = responses.calls[0].request
        assert req.headers["Content-Type"] == "application/x-www-form-urlencoded"
        body = req.body
        assert "grant_type=client_credentials" in body
        assert "client_id=test-client" in body
        assert "client_secret=test-secret" in body

    @responses.activate
    def test_token_caching(self):
        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_cached", "expires_in": 3600},
            status=200,
        )

        auth = make_auth()
        t1 = auth.get_access_token()
        t2 = auth.get_access_token()

        assert t1 == "tok_cached"
        assert t2 == "tok_cached"
        assert len(responses.calls) == 1

    @responses.activate
    def test_refresh_within_30s_buffer(self):
        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_1", "expires_in": 20},
            status=200,
        )
        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_2", "expires_in": 3600},
            status=200,
        )

        auth = make_auth()
        t1 = auth.get_access_token()
        assert t1 == "tok_1"

        # 20s expires_in < 30s buffer, so next call should refresh
        t2 = auth.get_access_token()
        assert t2 == "tok_2"
        assert len(responses.calls) == 2

    @responses.activate
    def test_no_refresh_when_token_valid(self):
        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_long", "expires_in": 3600},
            status=200,
        )

        auth = make_auth()
        auth.get_access_token()
        auth.get_access_token()
        auth.get_access_token()

        assert len(responses.calls) == 1

    @responses.activate
    def test_error_on_failed_request(self):
        responses.post(TOKEN_URL, json={"error": "invalid_client"}, status=401)

        auth = make_auth()
        with pytest.raises(AuthenticationError, match="Token request failed"):
            auth.get_access_token()

    @responses.activate
    def test_private_key_jwt_flow(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )

        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()

        responses.post(
            TOKEN_URL,
            json={"access_token": "tok_jwt", "expires_in": 3600},
            status=200,
        )

        auth = make_auth(client_secret=None, private_key=pem, kid="key-001")
        token = auth.get_access_token()

        assert token == "tok_jwt"
        body = responses.calls[0].request.body
        assert "client_assertion=" in body
        assert "client_assertion_type=" in body
        assert "client_secret" not in body

    @responses.activate
    def test_token_url_constructed_from_base_url(self):
        responses.post(
            "https://custom.api.com/oauth2/token",
            json={"access_token": "tok_custom", "expires_in": 3600},
            status=200,
        )

        auth = make_auth(base_url="https://custom.api.com")
        auth.get_access_token()

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://custom.api.com/oauth2/token"

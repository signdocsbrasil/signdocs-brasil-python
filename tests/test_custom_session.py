"""Tests for custom session support."""

from __future__ import annotations

from unittest.mock import MagicMock

import requests
import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil._http_client import HttpClient

BASE_URL = "https://api.signdocs.com.br"


def _make_auth() -> AuthHandler:
    auth = MagicMock(spec=AuthHandler)
    auth.get_access_token.return_value = "test-token"
    return auth


class TestCustomSession:
    @responses.activate
    def test_custom_session_is_used(self):
        """A user-supplied requests.Session should be used for HTTP calls."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        custom_session = requests.Session()
        custom_session.headers["X-Custom"] = "present"

        client = HttpClient(
            base_url=BASE_URL,
            timeout=30000,
            max_retries=0,
            auth=_make_auth(),
            session=custom_session,
        )
        client.request("GET", "/health", no_auth=True)

        req = responses.calls[0].request
        assert req.headers["X-Custom"] == "present"

    @responses.activate
    def test_custom_session_gets_user_agent(self):
        """Even with a custom session, the User-Agent header must be set."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        custom_session = requests.Session()
        client = HttpClient(
            base_url=BASE_URL,
            timeout=30000,
            max_retries=0,
            auth=_make_auth(),
            session=custom_session,
        )
        client.request("GET", "/health", no_auth=True)

        req = responses.calls[0].request
        assert "signdocs-brasil-python/" in req.headers["User-Agent"]

    @responses.activate
    def test_default_session_when_none_provided(self):
        """When no session is provided, a default session is created."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        client = HttpClient(
            base_url=BASE_URL,
            timeout=30000,
            max_retries=0,
            auth=_make_auth(),
        )
        client.request("GET", "/health", no_auth=True)

        req = responses.calls[0].request
        assert "signdocs-brasil-python/" in req.headers["User-Agent"]
        assert responses.calls[0].response.status_code == 200

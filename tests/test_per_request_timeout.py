"""Tests for per-request timeout override."""

from __future__ import annotations

from unittest.mock import MagicMock

import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil._http_client import HttpClient

BASE_URL = "https://api.signdocs.com.br"


def _make_auth() -> AuthHandler:
    auth = MagicMock(spec=AuthHandler)
    auth.get_access_token.return_value = "test-token"
    return auth


class TestPerRequestTimeout:
    @responses.activate
    def test_per_request_timeout_overrides_default(self):
        """A per-request timeout in milliseconds should override the client default."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        client = HttpClient(
            base_url=BASE_URL,
            timeout=30000,  # 30 seconds default
            max_retries=0,
            auth=_make_auth(),
        )
        client.request("GET", "/health", no_auth=True, timeout=5000)

        # The responses library records the timeout kwarg on the PreparedRequest
        # We can verify by checking the actual timeout used.
        # Since responses mocks the transport layer, we verify via the request
        # object attributes. The timeout is passed to session.request() as a kwarg.
        #
        # responses does not directly expose the timeout kwarg, so we use a
        # different approach: patch the session to inspect the call.
        pass  # Covered by the mock-based test below

    def test_per_request_timeout_converts_to_seconds(self):
        """Per-request timeout (ms) should be converted to seconds for requests."""
        import requests

        original_request = requests.Session.request
        captured_timeouts: list[float] = []

        def capture_request(self_session, *args, **kwargs):  # noqa: ARG001
            captured_timeouts.append(kwargs.get("timeout"))
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            resp.headers = {"Content-Type": "application/json"}
            resp.json.return_value = {"status": "ok"}
            return resp

        requests.Session.request = capture_request  # type: ignore[assignment]
        try:
            client = HttpClient(
                base_url=BASE_URL,
                timeout=30000,
                max_retries=0,
                auth=_make_auth(),
            )
            client.request("GET", "/health", no_auth=True, timeout=5000)

            assert len(captured_timeouts) == 1
            assert captured_timeouts[0] == 5.0  # 5000ms -> 5.0s
        finally:
            requests.Session.request = original_request  # type: ignore[assignment]

    def test_default_timeout_used_when_no_override(self):
        """When no per-request timeout is given, the client default is used."""
        import requests

        captured_timeouts: list[float] = []
        original_request = requests.Session.request

        def capture_request(self_session, *args, **kwargs):  # noqa: ARG001
            captured_timeouts.append(kwargs.get("timeout"))
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            resp.headers = {"Content-Type": "application/json"}
            resp.json.return_value = {"status": "ok"}
            return resp

        requests.Session.request = capture_request  # type: ignore[assignment]
        try:
            client = HttpClient(
                base_url=BASE_URL,
                timeout=15000,  # 15 seconds default
                max_retries=0,
                auth=_make_auth(),
            )
            client.request("GET", "/health", no_auth=True)

            assert len(captured_timeouts) == 1
            assert captured_timeouts[0] == 15.0  # 15000ms -> 15.0s
        finally:
            requests.Session.request = original_request  # type: ignore[assignment]

    def test_none_timeout_uses_default(self):
        """Explicitly passing timeout=None should use the client default."""
        import requests

        captured_timeouts: list[float] = []
        original_request = requests.Session.request

        def capture_request(self_session, *args, **kwargs):  # noqa: ARG001
            captured_timeouts.append(kwargs.get("timeout"))
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            resp.headers = {"Content-Type": "application/json"}
            resp.json.return_value = {"status": "ok"}
            return resp

        requests.Session.request = capture_request  # type: ignore[assignment]
        try:
            client = HttpClient(
                base_url=BASE_URL,
                timeout=20000,
                max_retries=0,
                auth=_make_auth(),
            )
            client.request("GET", "/health", no_auth=True, timeout=None)

            assert len(captured_timeouts) == 1
            assert captured_timeouts[0] == 20.0  # 20000ms -> 20.0s
        finally:
            requests.Session.request = original_request  # type: ignore[assignment]

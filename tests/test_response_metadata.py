"""Tests for ResponseMetadata parsing and the on_response callback plumbing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil._http_client import HttpClient
from signdocs_brasil.response_metadata import ResponseMetadata

BASE_URL = "https://api.signdocs.com.br"


def _mock_response(headers: dict[str, str], status: int = 200):
    class _Resp:
        def __init__(self) -> None:
            self.headers = headers
            self.status_code = status

    return _Resp()


class TestResponseMetadataParsing:
    def test_basic_fields(self):
        resp = _mock_response(
            {
                "RateLimit-Limit": "100",
                "RateLimit-Remaining": "42",
                "RateLimit-Reset": "60",
                "X-Request-Id": "req-abc",
            }
        )
        m = ResponseMetadata.from_response(resp, "get", "/v1/tx")
        assert m.rate_limit_limit == 100
        assert m.rate_limit_remaining == 42
        assert m.rate_limit_reset == 60
        assert m.request_id == "req-abc"
        assert m.status_code == 200
        assert m.method == "GET"
        assert m.path == "/v1/tx"

    def test_missing_headers_are_none(self):
        resp = _mock_response({})
        m = ResponseMetadata.from_response(resp, "POST", "/v1/tx")
        assert m.rate_limit_limit is None
        assert m.rate_limit_remaining is None
        assert m.rate_limit_reset is None
        assert m.deprecation is None
        assert m.sunset is None
        assert m.request_id is None

    def test_method_uppercased(self):
        resp = _mock_response({})
        m = ResponseMetadata.from_response(resp, "patch", "/v1/tx")
        assert m.method == "PATCH"

    def test_non_numeric_ratelimit_headers_become_none(self):
        resp = _mock_response({"RateLimit-Limit": "notanumber"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.rate_limit_limit is None

    def test_request_id_fallback_to_signdocs_specific_header(self):
        resp = _mock_response({"X-SignDocs-Request-Id": "sd-xyz"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.request_id == "sd-xyz"

    def test_request_id_prefers_standard_over_signdocs(self):
        resp = _mock_response(
            {"X-Request-Id": "standard", "X-SignDocs-Request-Id": "signdocs"}
        )
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.request_id == "standard"

    def test_deprecation_imf_fixdate(self):
        resp = _mock_response({"Deprecation": "Sun, 06 Nov 2025 08:49:37 GMT"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.deprecation is not None
        assert m.deprecation.tzinfo is not None
        assert m.deprecation.year == 2025
        assert m.deprecation.month == 11
        assert m.deprecation.day == 6

    def test_deprecation_unix_at_format(self):
        resp = _mock_response({"Deprecation": "@1735689600"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.deprecation is not None
        assert m.deprecation == datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_sunset_imf_fixdate(self):
        resp = _mock_response({"Sunset": "Wed, 11 Nov 2026 23:59:59 GMT"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.sunset is not None
        assert m.sunset.year == 2026

    def test_sunset_unix_at_format(self):
        resp = _mock_response({"Sunset": "@0"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.sunset is not None
        assert m.sunset == datetime(1970, 1, 1, tzinfo=timezone.utc)

    def test_unparseable_deprecation_returns_none(self):
        resp = _mock_response({"Deprecation": "not-a-date"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.deprecation is None

    def test_empty_deprecation_returns_none(self):
        resp = _mock_response({"Deprecation": "   "})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.deprecation is None

    def test_is_deprecated_true_when_deprecation_present(self):
        resp = _mock_response({"Deprecation": "@1735689600"})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.is_deprecated() is True

    def test_is_deprecated_false_when_absent(self):
        resp = _mock_response({})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        assert m.is_deprecated() is False

    def test_frozen(self):
        resp = _mock_response({})
        m = ResponseMetadata.from_response(resp, "GET", "/")
        with pytest.raises((AttributeError, Exception)):
            m.status_code = 500  # type: ignore[misc]


def _make_http(on_response=None, logger=None):
    auth = MagicMock(spec=AuthHandler)
    auth.get_access_token.return_value = "test-token"
    return HttpClient(
        base_url=BASE_URL,
        timeout=30000,
        max_retries=0,
        auth=auth,
        on_response=on_response,
        logger=logger,
    )


class TestOnResponseCallback:
    @responses.activate
    def test_callback_fires_on_success(self):
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"ok": True},
            status=200,
            headers={"RateLimit-Remaining": "99", "X-Request-Id": "rq-1"},
        )

        captured: list[ResponseMetadata] = []
        client = _make_http(on_response=captured.append)
        client.request("GET", "/v1/test")

        assert len(captured) == 1
        meta = captured[0]
        assert meta.status_code == 200
        assert meta.method == "GET"
        assert meta.path == "/v1/test"
        assert meta.rate_limit_remaining == 99
        assert meta.request_id == "rq-1"

    @responses.activate
    def test_callback_fires_on_error_response(self):
        from signdocs_brasil.errors import BadRequestError

        responses.post(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Bad", "status": 400},
            status=400,
        )

        captured: list[ResponseMetadata] = []
        client = _make_http(on_response=captured.append)
        with pytest.raises(BadRequestError):
            client.request("POST", "/v1/test")

        # Callback should still have fired before the error was raised
        assert len(captured) == 1
        assert captured[0].status_code == 400

    @responses.activate
    def test_callback_exception_does_not_break_request(self):
        responses.get(f"{BASE_URL}/v1/test", json={"ok": True}, status=200)

        def boom(_m):
            raise RuntimeError("observability is broken")

        logger = logging.getLogger("test-sdk-on-response")
        logger.addHandler(logging.NullHandler())
        client = _make_http(on_response=boom, logger=logger)

        # Should not raise
        result = client.request("GET", "/v1/test")
        assert result == {"ok": True}

    @responses.activate
    def test_no_callback_is_fine(self):
        responses.get(f"{BASE_URL}/v1/test", json={"ok": True}, status=200)

        client = _make_http(on_response=None)
        # Should not raise
        result = client.request("GET", "/v1/test")
        assert result == {"ok": True}

    @responses.activate
    def test_callback_fires_once_per_response(self):
        responses.get(f"{BASE_URL}/v1/a", json={}, status=200)
        responses.get(f"{BASE_URL}/v1/b", json={}, status=200)

        captured: list[ResponseMetadata] = []
        client = _make_http(on_response=captured.append)
        client.request("GET", "/v1/a")
        client.request("GET", "/v1/b")

        assert len(captured) == 2
        assert captured[0].path == "/v1/a"
        assert captured[1].path == "/v1/b"

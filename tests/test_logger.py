"""Tests for logger integration in HttpClient."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil._http_client import HttpClient

BASE_URL = "https://api.signdocs.com.br"


def _make_auth() -> AuthHandler:
    auth = MagicMock(spec=AuthHandler)
    auth.get_access_token.return_value = "test-token"
    return auth


def _make_client(logger: logging.Logger | None = None) -> HttpClient:
    return HttpClient(
        base_url=BASE_URL,
        timeout=30000,
        max_retries=0,
        auth=_make_auth(),
        logger=logger,
    )


class TestLoggerOnSuccess:
    @responses.activate
    def test_info_logged_on_success(self):
        """logger.info is called with method, path, status, duration on 2xx."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        logger = MagicMock(spec=logging.Logger)
        client = _make_client(logger)
        client.request("GET", "/health", no_auth=True)

        logger.info.assert_called_once()
        args = logger.info.call_args
        fmt = args[0][0]
        assert "method=%s" in fmt
        assert "path=%s" in fmt
        assert "status=%d" in fmt
        assert "duration_ms=%d" in fmt
        assert args[0][1] == "GET"
        assert args[0][2] == "/health"
        assert args[0][3] == 200

    @responses.activate
    def test_info_not_called_on_error(self):
        """logger.info is NOT called on error responses."""
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Not Found", "status": 404},
            status=404,
        )

        logger = MagicMock(spec=logging.Logger)
        client = _make_client(logger)

        try:
            client.request("GET", "/v1/test")
        except Exception:
            pass

        logger.info.assert_not_called()


class TestLoggerOnError:
    @responses.activate
    def test_warning_logged_on_4xx(self):
        """logger.warning is called on 4xx error responses."""
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Bad Request", "status": 400},
            status=400,
        )

        logger = MagicMock(spec=logging.Logger)
        client = _make_client(logger)

        try:
            client.request("GET", "/v1/test")
        except Exception:
            pass

        logger.warning.assert_called_once()
        args = logger.warning.call_args
        assert args[0][1] == "GET"
        assert args[0][2] == "/v1/test"
        assert args[0][3] == 400

    @responses.activate
    def test_warning_logged_on_5xx(self):
        """logger.warning is called on 5xx error responses."""
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Internal Server Error", "status": 500},
            status=500,
        )

        logger = MagicMock(spec=logging.Logger)
        client = _make_client(logger)

        try:
            client.request("GET", "/v1/test")
        except Exception:
            pass

        logger.warning.assert_called_once()
        args = logger.warning.call_args
        assert args[0][3] == 500


class TestLoggerSecurity:
    @responses.activate
    def test_authorization_header_not_logged(self):
        """Authorization header values must NEVER appear in log output."""
        responses.get(f"{BASE_URL}/v1/test", json={"ok": True}, status=200)

        logger = MagicMock(spec=logging.Logger)
        client = _make_client(logger)
        client.request("GET", "/v1/test")

        logger.info.assert_called_once()
        # Inspect the full formatted log message string
        log_call = logger.info.call_args
        fmt_string = log_call[0][0]
        format_args = log_call[0][1:]
        rendered = fmt_string % format_args
        assert "test-token" not in rendered
        assert "Bearer" not in rendered


class TestNoneLogger:
    @responses.activate
    def test_none_logger_does_not_error(self):
        """When logger is None, requests should succeed without errors."""
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        client = _make_client(logger=None)
        result = client.request("GET", "/health", no_auth=True)

        assert result["status"] == "ok"

    @responses.activate
    def test_none_logger_on_error_does_not_error(self):
        """When logger is None, error responses should still raise SDK errors."""
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Not Found", "status": 404},
            status=404,
        )

        client = _make_client(logger=None)

        from signdocs_brasil.errors import NotFoundError

        try:
            client.request("GET", "/v1/test")
        except NotFoundError:
            pass  # Expected
        except Exception as exc:
            raise AssertionError(f"Unexpected exception type: {type(exc).__name__}") from exc

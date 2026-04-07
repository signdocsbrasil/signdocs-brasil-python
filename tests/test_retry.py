"""Tests for retry logic."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from signdocs_brasil._retry import (
    _MAX_DELAY_SECONDS,
    calculate_delay,
    is_retryable_status,
    with_retry,
)
from signdocs_brasil.errors import TimeoutError


class TestIsRetryableStatus:
    @pytest.mark.parametrize("status", [429, 500, 503])
    def test_retryable_codes(self, status):
        assert is_retryable_status(status) is True

    @pytest.mark.parametrize("status", [200, 201, 204, 400, 401, 403, 404, 409, 422])
    def test_non_retryable_codes(self, status):
        assert is_retryable_status(status) is False


class TestCalculateDelay:
    def test_uses_retry_after_when_present(self):
        delay = calculate_delay(0, retry_after=5)
        assert delay == 5.0

    def test_exponential_backoff_without_retry_after(self):
        delay = calculate_delay(0)
        assert 1.0 <= delay <= 2.0  # 2^0 + [0,1) jitter

        delay = calculate_delay(1)
        assert 2.0 <= delay <= 3.0  # 2^1 + [0,1) jitter

        delay = calculate_delay(2)
        assert 4.0 <= delay <= 5.0  # 2^2 + [0,1) jitter

    def test_max_delay_cap(self):
        delay = calculate_delay(10)  # 2^10 = 1024, should be capped
        assert delay <= _MAX_DELAY_SECONDS


class TestWithRetry:
    def _mock_response(self, status_code, headers=None):
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status_code
        resp.headers = headers or {}
        return resp

    @patch("signdocs_brasil._retry.time.sleep")
    def test_returns_immediately_on_success(self, mock_sleep):
        resp = self._mock_response(200)
        fn = MagicMock(return_value=resp)

        result = with_retry(3, fn)

        assert result is resp
        assert fn.call_count == 1
        mock_sleep.assert_not_called()

    @patch("signdocs_brasil._retry.time.sleep")
    def test_returns_immediately_on_non_retryable_error(self, mock_sleep):
        resp = self._mock_response(400)
        fn = MagicMock(return_value=resp)

        result = with_retry(3, fn)

        assert result is resp
        assert fn.call_count == 1

    @patch("signdocs_brasil._retry.time.sleep")
    def test_retries_on_429(self, mock_sleep):
        resp_429 = self._mock_response(429, {"Retry-After": "0"})
        resp_200 = self._mock_response(200)
        fn = MagicMock(side_effect=[resp_429, resp_200])

        result = with_retry(3, fn)

        assert result is resp_200
        assert fn.call_count == 2

    @patch("signdocs_brasil._retry.time.sleep")
    def test_retries_on_500(self, mock_sleep):
        resp_500 = self._mock_response(500)
        resp_200 = self._mock_response(200)
        fn = MagicMock(side_effect=[resp_500, resp_200])

        result = with_retry(3, fn)

        assert result is resp_200
        assert fn.call_count == 2

    @patch("signdocs_brasil._retry.time.sleep")
    def test_retries_on_503(self, mock_sleep):
        resp_503 = self._mock_response(503)
        resp_200 = self._mock_response(200)
        fn = MagicMock(side_effect=[resp_503, resp_200])

        result = with_retry(3, fn)

        assert result is resp_200

    @patch("signdocs_brasil._retry.time.sleep")
    def test_stops_after_max_retries(self, mock_sleep):
        resp_500 = self._mock_response(500)
        fn = MagicMock(return_value=resp_500)

        result = with_retry(2, fn)

        assert result.status_code == 500
        assert fn.call_count == 3  # initial + 2 retries

    @patch("signdocs_brasil._retry.time.sleep")
    @patch("signdocs_brasil._retry.time.monotonic")
    def test_timeout_after_60s(self, mock_monotonic, mock_sleep):
        mock_monotonic.side_effect = [0.0, 61.0]  # start=0, check=61
        resp_500 = self._mock_response(500)
        fn = MagicMock(return_value=resp_500)

        with pytest.raises(TimeoutError, match="60s"):
            with_retry(5, fn)

    @patch("signdocs_brasil._retry.time.sleep")
    def test_respects_retry_after_header(self, mock_sleep):
        resp_429 = self._mock_response(429, {"Retry-After": "3"})
        resp_200 = self._mock_response(200)
        fn = MagicMock(side_effect=[resp_429, resp_200])

        with_retry(3, fn)

        mock_sleep.assert_called_once_with(3.0)

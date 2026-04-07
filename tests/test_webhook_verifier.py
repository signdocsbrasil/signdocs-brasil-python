"""Tests for webhook signature verification."""

import hashlib
import hmac
import time

from signdocs_brasil.webhook_verifier import verify_webhook_signature


def _sign(body: str, secret: str, timestamp: int) -> str:
    signing_input = f"{timestamp}.{body}"
    return hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        body = '{"event":"transaction.completed"}'
        secret = "whsec_test123"
        ts = int(time.time())
        sig = _sign(body, secret, ts)

        assert verify_webhook_signature(body, sig, str(ts), secret) is True

    def test_invalid_signature(self):
        body = '{"event":"transaction.completed"}'
        ts = int(time.time())

        assert verify_webhook_signature(body, "invalid_hex", str(ts), "secret") is False

    def test_expired_timestamp(self):
        body = '{"event":"test"}'
        secret = "whsec_test"
        ts = int(time.time()) - 400  # > 300s ago
        sig = _sign(body, secret, ts)

        assert verify_webhook_signature(body, sig, str(ts), secret) is False

    def test_future_timestamp(self):
        body = '{"event":"test"}'
        secret = "whsec_test"
        ts = int(time.time()) + 400  # > 300s in future
        sig = _sign(body, secret, ts)

        assert verify_webhook_signature(body, sig, str(ts), secret) is False

    def test_custom_tolerance(self):
        body = '{"event":"test"}'
        secret = "whsec_test"
        ts = int(time.time()) - 100
        sig = _sign(body, secret, ts)

        assert verify_webhook_signature(body, sig, str(ts), secret, tolerance_seconds=50) is False
        assert verify_webhook_signature(body, sig, str(ts), secret, tolerance_seconds=200) is True

    def test_wrong_secret(self):
        body = '{"event":"test"}'
        ts = int(time.time())
        sig = _sign(body, "correct_secret", ts)

        assert verify_webhook_signature(body, sig, str(ts), "wrong_secret") is False

    def test_non_numeric_timestamp(self):
        assert verify_webhook_signature("{}", "abc", "not-a-number", "secret") is False

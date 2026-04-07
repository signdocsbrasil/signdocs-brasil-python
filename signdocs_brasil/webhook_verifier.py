"""Webhook signature verification.

Verifies HMAC-SHA256 webhook signatures using constant-time comparison
and configurable timestamp tolerance.
"""

from __future__ import annotations

import hashlib
import hmac
import time

_DEFAULT_TOLERANCE_SECONDS = 300


def verify_webhook_signature(
    body: str,
    signature_header: str,
    timestamp_header: str,
    secret: str,
    *,
    tolerance_seconds: int = _DEFAULT_TOLERANCE_SECONDS,
) -> bool:
    """Verify a webhook delivery signature.

    The signing input is ``"{timestamp}.{body}"`` and the signature is an
    HMAC-SHA256 hex digest.

    Args:
        body: The raw request body string.
        signature_header: The ``X-Signature`` header value (hex digest).
        timestamp_header: The ``X-Timestamp`` header value (Unix epoch seconds).
        secret: The webhook secret (returned when the webhook was registered).
        tolerance_seconds: Maximum allowed age of the timestamp in seconds.
            Defaults to 300 (5 minutes).

    Returns:
        True if the signature is valid and the timestamp is within tolerance.
    """
    try:
        timestamp = int(timestamp_header)
    except (ValueError, TypeError):
        return False

    now = int(time.time())
    if abs(now - timestamp) > tolerance_seconds:
        return False

    signing_input = f"{timestamp}.{body}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature_header, expected)

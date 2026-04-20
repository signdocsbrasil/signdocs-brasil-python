"""Response-level metadata surfaced via the ``on_response`` callback.

Captures the headers that are typically consumed for observability and
lifecycle signaling: IETF ``RateLimit-*`` counters, RFC 8594 ``Deprecation``
and ``Sunset`` signaling, and the upstream request ID. The SDK does not
otherwise surface these headers to resource methods, so the ``on_response``
callback is the single place to plug in observability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import requests as _requests

_INT_HEADER_RE = re.compile(r"^-?\d+$")
_UNIX_AT_RE = re.compile(r"^@(-?\d+)$")


@dataclass(frozen=True)
class ResponseMetadata:
    """Immutable snapshot of response-level metadata.

    Attributes:
        rate_limit_limit: Parsed ``RateLimit-Limit`` header (per IETF draft).
        rate_limit_remaining: Parsed ``RateLimit-Remaining``.
        rate_limit_reset: Parsed ``RateLimit-Reset`` (seconds until reset).
        deprecation: Parsed ``Deprecation`` header (RFC 8594) as a timezone-
            aware :class:`datetime.datetime`, or ``None`` if absent or
            unparseable.
        sunset: Parsed ``Sunset`` header (RFC 8594).
        request_id: The upstream ``X-Request-Id`` or ``X-SignDocs-Request-Id``.
        status_code: HTTP status code.
        method: HTTP method (uppercased).
        path: Request path (with query string if any).
    """

    rate_limit_limit: int | None
    rate_limit_remaining: int | None
    rate_limit_reset: int | None
    deprecation: datetime | None
    sunset: datetime | None
    request_id: str | None
    status_code: int
    method: str
    path: str

    @classmethod
    def from_response(
        cls,
        response: _requests.Response,
        method: str,
        path: str,
    ) -> ResponseMetadata:
        """Construct a :class:`ResponseMetadata` from a ``requests.Response``.

        Args:
            response: The HTTP response.
            method: The HTTP method used for the request.
            path: The request path (with query string if any).
        """
        return cls(
            rate_limit_limit=_int_header(response.headers, "RateLimit-Limit"),
            rate_limit_remaining=_int_header(response.headers, "RateLimit-Remaining"),
            rate_limit_reset=_int_header(response.headers, "RateLimit-Reset"),
            deprecation=_rfc8594_date(response.headers.get("Deprecation")),
            sunset=_rfc8594_date(response.headers.get("Sunset")),
            request_id=_first_header(
                response.headers, ["X-Request-Id", "X-SignDocs-Request-Id"]
            ),
            status_code=response.status_code,
            method=method.upper(),
            path=path,
        )

    def is_deprecated(self) -> bool:
        """Return True if the endpoint carries a ``Deprecation`` header."""
        return self.deprecation is not None


def _int_header(headers: Any, name: str) -> int | None:
    raw = headers.get(name)
    if raw is None:
        return None
    raw = str(raw).strip()
    if raw == "":
        return None
    if not _INT_HEADER_RE.match(raw):
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _first_header(headers: Any, names: list[str]) -> str | None:
    for name in names:
        raw = headers.get(name)
        if raw is not None and str(raw).strip() != "":
            return str(raw)
    return None


def _rfc8594_date(raw: str | None) -> datetime | None:
    """Parse an RFC 8594 Deprecation/Sunset header.

    Accepts either an IMF-fixdate (HTTP-date, e.g.
    ``Sun, 06 Nov 1994 08:49:37 GMT``) or the ``@<unix-seconds>`` form.
    Returns ``None`` for any unparseable input.
    """
    if raw is None:
        return None
    raw = raw.strip()
    if raw == "":
        return None

    at_match = _UNIX_AT_RE.match(raw)
    if at_match is not None:
        try:
            return datetime.fromtimestamp(int(at_match.group(1)), tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            return None

    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None

    if parsed is None:
        return None

    # email.utils.parsedate_to_datetime returns naive datetime for dates
    # without an explicit timezone. RFC 8594 mandates GMT, so assume UTC.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed

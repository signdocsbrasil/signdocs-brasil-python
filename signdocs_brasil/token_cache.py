"""Pluggable OAuth2 access token cache.

The default implementation :class:`InMemoryTokenCache` scopes the cache to the
lifetime of a single Python process — this preserves the pre-1.3 behavior and
is appropriate for long-lived daemons and worker processes. Stateless hosts
(serverless, short-lived CLI invocations, per-request workers) should supply
an implementation backed by a shared store (Redis, memcached, filesystem,
etc.) to avoid fetching a fresh token on every request.

Implementations MUST be safe to call concurrently; a ``set()`` that races
with another ``set()`` for the same key should leave the cache in a
consistent state. Implementations SHOULD treat the key as opaque — the SDK
derives keys deterministically via :func:`derive_cache_key` from
``client_id + base_url + scopes`` and hashes the material so leaked cache
keys cannot be reversed to recover the client ID.
"""

from __future__ import annotations

import hashlib
import threading
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class CachedToken:
    """Immutable value object for a cached OAuth2 access token.

    Attributes:
        access_token: The bearer token string.
        expires_at: Absolute expiry timestamp in unix seconds (float).
    """

    access_token: str
    expires_at: float

    def is_expired(self, now: float, skew_seconds: int = 30) -> bool:
        """Return True if the token is expired (with a safety skew).

        Args:
            now: Current time in unix seconds.
            skew_seconds: Consider the token expired this many seconds
                before its actual ``expires_at`` so that callers have
                time to use the token before the server rejects it.
        """
        return now >= (self.expires_at - skew_seconds)


class TokenCache(ABC):
    """Abstract base class for a pluggable OAuth2 access token cache."""

    @abstractmethod
    def get(self, key: str) -> CachedToken | None:
        """Return the cached token for ``key``, or ``None`` if missing/expired.

        Implementations SHOULD return ``None`` (not raise) on any backend
        error so the SDK can transparently fall back to fetching a fresh
        token.
        """

    @abstractmethod
    def set(self, key: str, token: CachedToken) -> None:
        """Store ``token`` under ``key``.

        Implementations SHOULD honor ``token.expires_at`` as an upper bound
        on storage TTL.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the cached entry for ``key``. Idempotent."""


class InMemoryTokenCache(TokenCache):
    """Default in-process token cache.

    Thread-safe via a :class:`threading.Lock`. Equivalent to the behavior
    the SDK shipped with in 1.2.x and earlier — cache lives for the
    lifetime of the Python process.
    """

    def __init__(self) -> None:
        self._store: dict[str, CachedToken] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> CachedToken | None:
        import time

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.is_expired(time.time(), skew_seconds=0):
                del self._store[key]
                return None
            return entry

    def set(self, key: str, token: CachedToken) -> None:
        with self._lock:
            self._store[key] = token

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)


def derive_cache_key(client_id: str, base_url: str, scopes: Iterable[str]) -> str:
    """Derive a deterministic cache key from credentials + base URL + scopes.

    Produces ``signdocs.oauth.<32-hex-chars>`` where the hex chars are the
    first 32 of SHA-256 over the canonical material. Hashing ensures a
    leaked cache key cannot be reversed to recover the client ID.

    Args:
        client_id: The OAuth2 client ID.
        base_url: The API base URL. A trailing slash is stripped so
            ``https://api.example.com`` and ``https://api.example.com/``
            produce the same key.
        scopes: The requested OAuth2 scopes. Order is normalized by
            sorting before hashing, so the same scope set always produces
            the same key regardless of input order.

    Returns:
        A cache key of the form ``signdocs.oauth.<hex32>``.
    """
    canonical_scopes = sorted(scopes)
    material = f"{client_id}|{base_url.rstrip('/')}|{' '.join(canonical_scopes)}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"signdocs.oauth.{digest[:32]}"

"""OAuth2 authentication handler with pluggable token caching.

Supports both ``client_secret`` and ``private_key_jwt`` (ES256) authentication
modes. Tokens are stored via a pluggable :class:`TokenCache` — the default
:class:`InMemoryTokenCache` preserves the pre-1.3 behavior of a per-process
cache. Stateless hosts (serverless, per-request workers) should inject a
shared-store implementation (Redis, filesystem, etc.) to avoid fetching a
fresh token on every request.

Concurrent callers waiting on a refresh share a single in-flight token
request via a per-handler ``Event``.
"""

from __future__ import annotations

import threading
import time
import uuid

import jwt
import requests as _requests

from .errors import AuthenticationError
from .token_cache import CachedToken, InMemoryTokenCache, TokenCache, derive_cache_key

_TOKEN_REFRESH_BUFFER_SECONDS = 30


class AuthHandler:
    """Handles OAuth2 client credentials token acquisition and caching.

    Args:
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret (mutually exclusive with
            ``private_key``).
        private_key: PEM-encoded ES256 private key for JWT assertion.
        kid: Key ID header for the JWT.
        base_url: API base URL used to construct the token endpoint.
        scopes: OAuth2 scopes to request.
        cache: Optional pluggable :class:`TokenCache`. Defaults to a
            fresh :class:`InMemoryTokenCache` when ``None``.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str | None = None,
        private_key: str | None = None,
        kid: str | None = None,
        base_url: str,
        scopes: list[str],
        cache: TokenCache | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._private_key = private_key
        self._kid = kid
        self._base_url = base_url
        self._token_url = f"{base_url.rstrip('/')}/oauth2/token"
        self._scopes = scopes

        self._cache: TokenCache = cache if cache is not None else InMemoryTokenCache()
        self._cache_key = derive_cache_key(client_id, base_url, scopes)

        self._lock = threading.Lock()
        self._refresh_event: threading.Event | None = None
        self._refresh_result: str | None = None
        self._refresh_error: Exception | None = None

    def get_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary.

        Thread-safe: if multiple threads call this concurrently while the
        cached token is expired, only one will perform the refresh; the
        others will wait on the in-flight request and reuse its result.

        Returns:
            A valid Bearer access token string.

        Raises:
            AuthenticationError: If the token request fails.
        """
        cached = self._cache.get(self._cache_key)
        if cached is not None and not cached.is_expired(
            time.time(), skew_seconds=_TOKEN_REFRESH_BUFFER_SECONDS
        ):
            return cached.access_token

        with self._lock:
            # Double-check after acquiring the lock.
            cached = self._cache.get(self._cache_key)
            if cached is not None and not cached.is_expired(
                time.time(), skew_seconds=_TOKEN_REFRESH_BUFFER_SECONDS
            ):
                return cached.access_token

            # If another thread is already refreshing, wait on its event.
            if self._refresh_event is not None:
                event = self._refresh_event
                self._lock.release()
                try:
                    event.wait()
                    if self._refresh_error is not None:
                        raise self._refresh_error
                    assert self._refresh_result is not None
                    return self._refresh_result
                finally:
                    self._lock.acquire()

            # We are the refresher.
            event = threading.Event()
            self._refresh_event = event
            self._refresh_error = None
            self._refresh_result = None

        # Perform the refresh outside the lock.
        try:
            token = self._fetch_token()
            self._refresh_result = token
            return token
        except Exception as exc:
            self._refresh_error = exc
            raise
        finally:
            event.set()
            with self._lock:
                self._refresh_event = None

    def invalidate(self) -> None:
        """Invalidate the cached token.

        The next call to :meth:`get_access_token` will fetch a fresh token
        from the authorization server.
        """
        self._cache.delete(self._cache_key)

    def _fetch_token(self) -> str:
        """Perform the OAuth2 client_credentials token exchange.

        Returns:
            The access token string.

        Raises:
            AuthenticationError: On non-2xx responses.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "scope": " ".join(self._scopes),
        }

        if self._client_secret:
            data["client_secret"] = self._client_secret
        elif self._private_key and self._kid:
            assertion = self._build_jwt_assertion()
            data["client_assertion_type"] = (
                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            )
            data["client_assertion"] = assertion

        try:
            response = _requests.post(
                self._token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
        except _requests.RequestException as exc:
            raise AuthenticationError(f"Token request failed: {exc}") from exc

        if not response.ok:
            raise AuthenticationError(
                f"Token request failed ({response.status_code}): {response.text}"
            )

        token_data = response.json()
        access_token: str = token_data["access_token"]
        expires_in: int = token_data["expires_in"]

        self._cache.set(
            self._cache_key,
            CachedToken(access_token=access_token, expires_at=time.time() + expires_in),
        )

        return access_token

    def _build_jwt_assertion(self) -> str:
        """Build an ES256-signed JWT client assertion for private_key_jwt auth.

        Returns:
            The signed JWT string.
        """
        now = int(time.time())
        payload = {
            "iss": self._client_id,
            "sub": self._client_id,
            "aud": self._token_url,
            "exp": now + 300,
            "iat": now,
            "jti": str(uuid.uuid4()),
        }
        headers = {
            "alg": "ES256",
            "typ": "JWT",
            "kid": self._kid,
        }

        return jwt.encode(
            payload,
            self._private_key,  # type: ignore[arg-type]
            algorithm="ES256",
            headers=headers,
        )

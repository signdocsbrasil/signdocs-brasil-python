"""Tests for the pluggable OAuth token cache."""

from __future__ import annotations

import time

import pytest
import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil.token_cache import (
    CachedToken,
    InMemoryTokenCache,
    TokenCache,
    derive_cache_key,
)

TOKEN_URL = "https://api.signdocs.com.br/oauth2/token"


class TestCachedToken:
    def test_is_expired_true_when_now_past_expires_at(self):
        token = CachedToken(access_token="x", expires_at=100.0)
        assert token.is_expired(now=101.0, skew_seconds=0) is True

    def test_is_expired_false_when_now_before_expires_at(self):
        token = CachedToken(access_token="x", expires_at=100.0)
        assert token.is_expired(now=50.0, skew_seconds=0) is False

    def test_is_expired_honors_skew(self):
        token = CachedToken(access_token="x", expires_at=100.0)
        # With 30s skew, token is "expired" once now >= 70
        assert token.is_expired(now=69.0, skew_seconds=30) is False
        assert token.is_expired(now=71.0, skew_seconds=30) is True

    def test_frozen(self):
        token = CachedToken(access_token="x", expires_at=100.0)
        with pytest.raises((AttributeError, Exception)):
            token.access_token = "y"  # type: ignore[misc]


class TestInMemoryTokenCache:
    def test_get_miss_returns_none(self):
        cache = InMemoryTokenCache()
        assert cache.get("missing") is None

    def test_set_then_get(self):
        cache = InMemoryTokenCache()
        future_expiry = time.time() + 3600
        token = CachedToken(access_token="abc", expires_at=future_expiry)
        cache.set("k1", token)
        got = cache.get("k1")
        assert got is not None
        assert got.access_token == "abc"

    def test_get_expired_returns_none_and_evicts(self):
        cache = InMemoryTokenCache()
        past_expiry = time.time() - 10
        cache.set("k1", CachedToken(access_token="old", expires_at=past_expiry))
        assert cache.get("k1") is None
        # Still None on subsequent get
        assert cache.get("k1") is None

    def test_delete_idempotent(self):
        cache = InMemoryTokenCache()
        cache.delete("never-existed")  # no-op, should not raise
        cache.set("k1", CachedToken(access_token="x", expires_at=time.time() + 100))
        cache.delete("k1")
        assert cache.get("k1") is None
        cache.delete("k1")  # idempotent

    def test_is_tokencache_subclass(self):
        assert issubclass(InMemoryTokenCache, TokenCache)


class TestDeriveCacheKey:
    def test_deterministic(self):
        k1 = derive_cache_key("client-A", "https://api.example.com", ["a", "b"])
        k2 = derive_cache_key("client-A", "https://api.example.com", ["a", "b"])
        assert k1 == k2

    def test_scope_order_normalized(self):
        k1 = derive_cache_key("c", "https://api.example.com", ["a", "b", "c"])
        k2 = derive_cache_key("c", "https://api.example.com", ["c", "b", "a"])
        assert k1 == k2

    def test_trailing_slash_normalized(self):
        k1 = derive_cache_key("c", "https://api.example.com", ["x"])
        k2 = derive_cache_key("c", "https://api.example.com/", ["x"])
        assert k1 == k2

    def test_has_expected_prefix(self):
        key = derive_cache_key("c", "https://api.example.com", ["x"])
        assert key.startswith("signdocs.oauth.")

    def test_hex_length_32(self):
        key = derive_cache_key("c", "https://api.example.com", ["x"])
        hex_part = key.removeprefix("signdocs.oauth.")
        assert len(hex_part) == 32
        # Characters are lowercase hex
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_does_not_leak_client_id(self):
        secret_client_id = "super-secret-client-id-do-not-leak-xyz"
        key = derive_cache_key(secret_client_id, "https://api.example.com", ["x"])
        assert secret_client_id not in key

    def test_different_clients_different_keys(self):
        k1 = derive_cache_key("c1", "https://api.example.com", ["x"])
        k2 = derive_cache_key("c2", "https://api.example.com", ["x"])
        assert k1 != k2

    def test_different_scopes_different_keys(self):
        k1 = derive_cache_key("c", "https://api.example.com", ["a"])
        k2 = derive_cache_key("c", "https://api.example.com", ["b"])
        assert k1 != k2

    def test_different_base_urls_different_keys(self):
        k1 = derive_cache_key("c", "https://api.example.com", ["x"])
        k2 = derive_cache_key("c", "https://other.example.com", ["x"])
        assert k1 != k2


def _make_auth(cache: TokenCache | None = None, **kwargs) -> AuthHandler:
    defaults = {
        "client_id": "test-client",
        "client_secret": "test-secret",
        "base_url": "https://api.signdocs.com.br",
        "scopes": ["transactions:read"],
    }
    defaults.update(kwargs)
    return AuthHandler(cache=cache, **defaults)


class TestAuthCacheIntegration:
    @responses.activate
    def test_cache_hit_avoids_network(self):
        cache = InMemoryTokenCache()
        # Pre-seed the cache with a valid token
        key = derive_cache_key(
            "test-client", "https://api.signdocs.com.br", ["transactions:read"]
        )
        cache.set(key, CachedToken(access_token="pre-seeded", expires_at=time.time() + 3600))

        auth = _make_auth(cache=cache)
        token = auth.get_access_token()

        assert token == "pre-seeded"
        assert len(responses.calls) == 0  # No network

    @responses.activate
    def test_cache_miss_fetches_and_stores(self):
        responses.post(
            TOKEN_URL, json={"access_token": "tok_new", "expires_in": 3600}, status=200
        )
        cache = InMemoryTokenCache()
        auth = _make_auth(cache=cache)

        t1 = auth.get_access_token()
        assert t1 == "tok_new"
        assert len(responses.calls) == 1

        # Second call should hit the cache
        t2 = auth.get_access_token()
        assert t2 == "tok_new"
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_expired_triggers_refresh(self):
        responses.post(
            TOKEN_URL, json={"access_token": "tok_fresh", "expires_in": 3600}, status=200
        )
        cache = InMemoryTokenCache()
        key = derive_cache_key(
            "test-client", "https://api.signdocs.com.br", ["transactions:read"]
        )
        # Seed with an expired token
        cache.set(key, CachedToken(access_token="tok_old", expires_at=time.time() - 100))

        auth = _make_auth(cache=cache)
        token = auth.get_access_token()

        assert token == "tok_fresh"
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_within_skew_buffer_triggers_refresh(self):
        responses.post(
            TOKEN_URL, json={"access_token": "tok_refreshed", "expires_in": 3600}, status=200
        )
        cache = InMemoryTokenCache()
        key = derive_cache_key(
            "test-client", "https://api.signdocs.com.br", ["transactions:read"]
        )
        # Within the 30s skew: should still be considered expired
        cache.set(key, CachedToken(access_token="tok_soon", expires_at=time.time() + 10))

        auth = _make_auth(cache=cache)
        token = auth.get_access_token()

        assert token == "tok_refreshed"

    @responses.activate
    def test_cache_shared_across_auth_instances(self):
        """Two AuthHandler instances with identical credentials share a cache."""
        responses.post(
            TOKEN_URL, json={"access_token": "tok_shared", "expires_in": 3600}, status=200
        )

        shared_cache = InMemoryTokenCache()
        auth1 = _make_auth(cache=shared_cache)
        auth2 = _make_auth(cache=shared_cache)

        t1 = auth1.get_access_token()
        t2 = auth2.get_access_token()

        assert t1 == t2 == "tok_shared"
        # Only one network call despite two handlers
        assert len(responses.calls) == 1

    @responses.activate
    def test_invalidate_deletes_cached_entry(self):
        responses.post(
            TOKEN_URL, json={"access_token": "tok_first", "expires_in": 3600}, status=200
        )
        responses.post(
            TOKEN_URL, json={"access_token": "tok_second", "expires_in": 3600}, status=200
        )

        cache = InMemoryTokenCache()
        auth = _make_auth(cache=cache)

        assert auth.get_access_token() == "tok_first"
        assert len(responses.calls) == 1

        auth.invalidate()

        assert auth.get_access_token() == "tok_second"
        assert len(responses.calls) == 2

    @responses.activate
    def test_default_cache_is_inmemory(self):
        """AuthHandler with no cache argument falls back to InMemoryTokenCache."""
        responses.post(
            TOKEN_URL, json={"access_token": "tok", "expires_in": 3600}, status=200
        )
        auth = _make_auth()  # No cache argument
        token = auth.get_access_token()
        assert token == "tok"
        # Still caches by default
        auth.get_access_token()
        assert len(responses.calls) == 1

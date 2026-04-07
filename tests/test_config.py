"""Tests for client configuration."""

import pytest

from signdocs_brasil._config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_SCOPES,
    DEFAULT_TIMEOUT,
    ClientConfig,
    resolve_config,
)


class TestClientConfig:
    def test_defaults(self):
        config = ClientConfig(client_id="test", client_secret="secret")
        assert config.base_url == DEFAULT_BASE_URL
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.max_retries == DEFAULT_MAX_RETRIES
        assert config.scopes == DEFAULT_SCOPES

    def test_custom_values(self):
        config = ClientConfig(
            client_id="my-client",
            client_secret="my-secret",
            base_url="https://custom.api.com",
            timeout=5000,
            max_retries=3,
            scopes=["custom:scope"],
        )
        assert config.base_url == "https://custom.api.com"
        assert config.timeout == 5000
        assert config.max_retries == 3
        assert config.scopes == ["custom:scope"]


class TestResolveConfig:
    def test_valid_with_client_secret(self):
        config = ClientConfig(client_id="test", client_secret="secret")
        result = resolve_config(config)
        assert result.client_id == "test"
        assert result.client_secret == "secret"

    def test_valid_with_private_key(self):
        config = ClientConfig(client_id="test", private_key="pem-data", kid="key-1")
        result = resolve_config(config)
        assert result.private_key == "pem-data"
        assert result.kid == "key-1"

    def test_missing_client_id_raises(self):
        config = ClientConfig(client_id="", client_secret="secret")
        with pytest.raises(ValueError, match="client_id is required"):
            resolve_config(config)

    def test_no_auth_raises(self):
        config = ClientConfig(client_id="test")
        with pytest.raises(ValueError, match="Either client_secret or private_key"):
            resolve_config(config)

    def test_private_key_without_kid_raises(self):
        config = ClientConfig(client_id="test", private_key="pem-data")
        with pytest.raises(ValueError, match="kid is required"):
            resolve_config(config)

    def test_scopes_default_is_independent_copy(self):
        c1 = ClientConfig(client_id="a", client_secret="s")
        c2 = ClientConfig(client_id="b", client_secret="s")
        c1.scopes.append("extra")
        assert "extra" not in c2.scopes

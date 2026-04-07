"""Client configuration and defaults."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

DEFAULT_BASE_URL = "https://api.signdocs.com.br"
DEFAULT_TIMEOUT = 30_000  # milliseconds
DEFAULT_MAX_RETRIES = 5
DEFAULT_SCOPES = [
    "transactions:read",
    "transactions:write",
    "steps:write",
    "evidence:read",
    "webhooks:write",
]


@dataclass
class ClientConfig:
    """Configuration for the SignDocs Brasil API client.

    Either ``client_secret`` or ``private_key`` + ``kid`` must be provided.

    Args:
        client_id: OAuth2 client ID.
        client_secret: OAuth2 client secret (for client_secret auth mode).
        private_key: PEM-encoded ES256 private key (for private_key_jwt auth mode).
        kid: Key ID for the private key.
        base_url: API base URL. Defaults to ``https://api.signdocs.com.br``.
        timeout: Request timeout in milliseconds. Defaults to 30000.
        max_retries: Maximum number of retries for retryable errors. Defaults to 5.
        scopes: OAuth2 scopes to request.
        session: Optional custom ``requests.Session`` to use for HTTP calls.
        logger: Optional ``logging.Logger`` for request/response logging.
    """

    client_id: str
    client_secret: str | None = None
    private_key: str | None = None
    kid: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    scopes: list[str] = field(default_factory=lambda: list(DEFAULT_SCOPES))
    session: requests.Session | None = None
    logger: logging.Logger | None = None


def resolve_config(config: ClientConfig) -> ClientConfig:
    """Validate and resolve a client configuration, applying defaults.

    Args:
        config: The user-supplied configuration.

    Returns:
        The validated configuration (same instance, mutated if needed).

    Raises:
        ValueError: If required fields are missing or inconsistent.
    """
    if not config.client_id:
        raise ValueError("client_id is required")
    if not config.client_secret and not config.private_key:
        raise ValueError("Either client_secret or private_key+kid is required")
    if config.private_key and not config.kid:
        raise ValueError("kid is required when using private_key")
    return config

"""SignDocs Brasil Python SDK.

Official Python client for the SignDocs Brasil electronic signature API.

Example::

    from signdocs_brasil import SignDocsBrasilClient, ClientConfig

    client = SignDocsBrasilClient(ClientConfig(
        client_id="your-client-id",
        client_secret="your-client-secret",
    ))

    # Check API health
    health = client.health.check()

    # Create a transaction
    from signdocs_brasil.models import (
        CreateTransactionRequest,
        Policy,
        Signer,
    )

    tx = client.transactions.create(CreateTransactionRequest(
        purpose="DOCUMENT_SIGNATURE",
        policy=Policy(profile="CLICK_ONLY"),
        signer=Signer(
            name="Fulano de Tal",
            user_external_id="user-123",
            email="fulano@example.com",
        ),
    ))
"""

from ._config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    ClientConfig,
)
from .client import SignDocsBrasilClient
from .errors import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ConnectionError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    ProblemDetail,
    RateLimitError,
    ServiceUnavailableError,
    SignDocsBrasilApiError,
    SignDocsBrasilError,
    TimeoutError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from .response_metadata import ResponseMetadata
from .token_cache import CachedToken, InMemoryTokenCache, TokenCache
from .webhook_verifier import verify_webhook_signature

__version__ = "1.5.0"

__all__ = [
    # Client
    "SignDocsBrasilClient",
    # Config
    "ClientConfig",
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    # Errors
    "SignDocsBrasilError",
    "SignDocsBrasilApiError",
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "ServiceUnavailableError",
    "AuthenticationError",
    "ConnectionError",
    "TimeoutError",
    "ProblemDetail",
    # Token cache
    "TokenCache",
    "CachedToken",
    "InMemoryTokenCache",
    # Response metadata
    "ResponseMetadata",
    # Webhook
    "verify_webhook_signature",
    # Version
    "__version__",
]

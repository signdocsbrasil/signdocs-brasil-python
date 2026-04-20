"""Main client entry point for the SignDocs Brasil API."""

from __future__ import annotations

from ._auth import AuthHandler
from ._config import ClientConfig, resolve_config
from ._http_client import HttpClient
from .resources.document_groups import DocumentGroupsResource
from .resources.documents import DocumentsResource
from .resources.envelopes import EnvelopesResource
from .resources.evidence import EvidenceResource
from .resources.health import HealthResource
from .resources.signing import SigningResource
from .resources.signing_sessions import SigningSessionsResource
from .resources.steps import StepsResource
from .resources.transactions import TransactionsResource
from .resources.users import UsersResource
from .resources.verification import VerificationResource
from .resources.webhooks import WebhooksResource


class SignDocsBrasilClient:
    """Client for the SignDocs Brasil API.

    Provides access to all API resources through typed resource attributes.

    Example usage with client_secret::

        from signdocs_brasil import SignDocsBrasilClient, ClientConfig

        client = SignDocsBrasilClient(ClientConfig(
            client_id="your-client-id",
            client_secret="your-client-secret",
        ))

        health = client.health.check()
        print(health.status)

    Example usage with private_key_jwt (ES256)::

        client = SignDocsBrasilClient(ClientConfig(
            client_id="your-client-id",
            private_key=open("private-key.pem").read(),
            kid="your-key-id",
        ))

    Args:
        config: Client configuration with credentials and options.

    Raises:
        ValueError: If the configuration is invalid.
    """

    def __init__(self, config: ClientConfig) -> None:
        resolved = resolve_config(config)

        auth = AuthHandler(
            client_id=resolved.client_id,
            client_secret=resolved.client_secret,
            private_key=resolved.private_key,
            kid=resolved.kid,
            base_url=resolved.base_url,
            scopes=resolved.scopes,
            cache=resolved.token_cache,
        )

        http = HttpClient(
            base_url=resolved.base_url,
            timeout=resolved.timeout,
            max_retries=resolved.max_retries,
            auth=auth,
            session=resolved.session,
            logger=resolved.logger,
            on_response=resolved.on_response,
        )

        self.health: HealthResource = HealthResource(http)
        self.transactions: TransactionsResource = TransactionsResource(http)
        self.documents: DocumentsResource = DocumentsResource(http)
        self.steps: StepsResource = StepsResource(http)
        self.signing: SigningResource = SigningResource(http)
        self.signing_sessions: SigningSessionsResource = SigningSessionsResource(http)
        self.evidence: EvidenceResource = EvidenceResource(http)
        self.verification: VerificationResource = VerificationResource(http)
        self.users: UsersResource = UsersResource(http)
        self.webhooks: WebhooksResource = WebhooksResource(http)
        self.document_groups: DocumentGroupsResource = DocumentGroupsResource(http)
        self.envelopes: EnvelopesResource = EnvelopesResource(http)

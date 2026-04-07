"""Tests for the main SignDocsBrasilClient."""

import pytest

from signdocs_brasil._config import ClientConfig
from signdocs_brasil.client import SignDocsBrasilClient
from signdocs_brasil.resources.document_groups import DocumentGroupsResource
from signdocs_brasil.resources.documents import DocumentsResource
from signdocs_brasil.resources.evidence import EvidenceResource
from signdocs_brasil.resources.health import HealthResource
from signdocs_brasil.resources.signing import SigningResource
from signdocs_brasil.resources.steps import StepsResource
from signdocs_brasil.resources.transactions import TransactionsResource
from signdocs_brasil.resources.users import UsersResource
from signdocs_brasil.resources.verification import VerificationResource
from signdocs_brasil.resources.webhooks import WebhooksResource


class TestSignDocsBrasilClient:
    def test_creates_all_resources(self):
        client = SignDocsBrasilClient(
            ClientConfig(client_id="test", client_secret="secret"),
        )

        assert isinstance(client.health, HealthResource)
        assert isinstance(client.transactions, TransactionsResource)
        assert isinstance(client.documents, DocumentsResource)
        assert isinstance(client.steps, StepsResource)
        assert isinstance(client.signing, SigningResource)
        assert isinstance(client.evidence, EvidenceResource)
        assert isinstance(client.verification, VerificationResource)
        assert isinstance(client.users, UsersResource)
        assert isinstance(client.webhooks, WebhooksResource)
        assert isinstance(client.document_groups, DocumentGroupsResource)

    def test_invalid_config_raises(self):
        with pytest.raises(ValueError):
            SignDocsBrasilClient(ClientConfig(client_id="", client_secret="secret"))

    def test_no_auth_raises(self):
        with pytest.raises(ValueError):
            SignDocsBrasilClient(ClientConfig(client_id="test"))

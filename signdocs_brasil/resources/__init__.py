"""Resource classes for SignDocs Brasil SDK."""

from .document_groups import DocumentGroupsResource
from .documents import DocumentsResource
from .envelopes import EnvelopesResource
from .evidence import EvidenceResource
from .health import HealthResource
from .signing import SigningResource
from .steps import StepsResource
from .transactions import TransactionsResource
from .users import UsersResource
from .verification import VerificationResource
from .webhooks import WebhooksResource

__all__ = [
    "HealthResource",
    "TransactionsResource",
    "DocumentsResource",
    "StepsResource",
    "SigningResource",
    "EvidenceResource",
    "VerificationResource",
    "UsersResource",
    "WebhooksResource",
    "DocumentGroupsResource",
    "EnvelopesResource",
]

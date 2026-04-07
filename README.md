# signdocs-brasil

SDK oficial em Python para a API SignDocsBrasil.

## Requisitos

- Python 3.9+
- Dependências: `requests`, `PyJWT`, `cryptography`

## Instalação

```bash
pip install signdocs-brasil
```

## Início Rápido

```python
from signdocs_brasil import SignDocsBrasilClient, ClientConfig
from signdocs_brasil.models import (
    CreateTransactionRequest, Policy, Signer, InlineDocument,
)

client = SignDocsBrasilClient(ClientConfig(
    client_id='seu_client_id',
    client_secret='seu_client_secret',
))

tx = client.transactions.create(CreateTransactionRequest(
    purpose='DOCUMENT_SIGNATURE',
    policy=Policy(profile='CLICK_ONLY'),
    signer=Signer(
        name='João Silva',
        email='joao@example.com',
        user_external_id='user-001',
    ),
    document=InlineDocument(content=pdf_base64, filename='contrato.pdf'),
))

print(tx.transaction_id, tx.status)
```

### Private Key JWT (ES256)

```python
client = SignDocsBrasilClient(ClientConfig(
    client_id='seu_client_id',
    private_key=open('./private-key.pem').read(),
    kid='seu-key-id',
))
```

## Recursos Disponíveis

| Recurso | Métodos |
|---------|---------|
| `client.transactions` | `create`, `list`, `get`, `cancel`, `finalize`, `list_auto_paginate` |
| `client.documents` | `upload`, `presign`, `confirm`, `download` |
| `client.steps` | `list`, `start`, `complete` |
| `client.signing` | `prepare`, `complete` |
| `client.evidence` | `get` |
| `client.verification` | `verify`, `downloads` |
| `client.users` | `enroll` |
| `client.webhooks` | `register`, `list`, `delete`, `test` |
| `client.signing_sessions` | `create`, `get_status`, `cancel`, `list`, `wait_for_completion` |
| `client.envelopes` | `create`, `get`, `add_session`, `combined_stamp` |
| `client.document_groups` | `combined_stamp` |
| `client.health` | `check`, `history` |

## Assinatura Expressa (Sessões de Assinatura)

```python
from signdocs_brasil.models import (
    CreateSigningSessionRequest, SignerRequest, PolicyRequest, DocumentRequest,
)

session = client.signing_sessions.create(CreateSigningSessionRequest(
    purpose='DOCUMENT_SIGNATURE',
    policy=PolicyRequest(profile='BIOMETRIC'),
    signer=SignerRequest(name='João Silva', user_external_id='user-001', email='joao@example.com'),
    document=DocumentRequest(content=pdf_base64, filename='contrato.pdf'),
    return_url='https://meusite.com.br/assinado',
))
print(session.url)  # URL da página de assinatura hospedada
```

## Envelopes (Múltiplos Signatários)

```python
from signdocs_brasil.models import CreateEnvelopeRequest, AddEnvelopeSessionRequest

envelope = client.envelopes.create(CreateEnvelopeRequest(
    signing_mode='PARALLEL',
    total_signers=2,
    document_content=pdf_base64,
    document_filename='contrato.pdf',
))

session1 = client.envelopes.add_session(envelope.envelope_id, AddEnvelopeSessionRequest(
    signer_name='João Silva',
    signer_email='joao@example.com',
    policy_profile='CLICK_ONLY',
))

session2 = client.envelopes.add_session(envelope.envelope_id, AddEnvelopeSessionRequest(
    signer_name='Maria Santos',
    signer_email='maria@example.com',
    policy_profile='CLICK_ONLY',
    signer_index=2,
))

print(session1.url, session2.url)
```

## Configuração Avançada

### Session customizada

Injete um `requests.Session` customizado (ex: para proxying, certificados mTLS ou métricas):

```python
import requests
from signdocs_brasil import SignDocsBrasilClient, ClientConfig

session = requests.Session()
session.verify = '/path/to/ca-bundle.crt'

client = SignDocsBrasilClient(ClientConfig(
    client_id='seu_client_id',
    client_secret='seu_client_secret',
    session=session,
))
```

### Logging

O SDK aceita um `logging.Logger` padrão do Python. São logados apenas: método HTTP, path, status code e duração. Headers de autorização, corpos de request/response e tokens nunca são logados.

```python
import logging
from signdocs_brasil import SignDocsBrasilClient, ClientConfig

logger = logging.getLogger('signdocs')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

client = SignDocsBrasilClient(ClientConfig(
    client_id='seu_client_id',
    client_secret='seu_client_secret',
    logger=logger,
))
```

### Timeout por requisição

Todas as operações aceitam `timeout` (em milissegundos) como keyword argument, que sobrescreve o timeout padrão do client:

```python
tx = client.transactions.get('tx_123', timeout=5000)
```

## Documentação

Para guias completos de integração com exemplos passo-a-passo de todos os fluxos de assinatura, veja a [documentação centralizada](../docs/README.md).

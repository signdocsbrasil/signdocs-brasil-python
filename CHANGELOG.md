# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.11.0] - 2026-08-31

### Added

- **Enrollment read and erase** — `GET` and `DELETE` on
  `/v1/users/{userExternalId}/enrollment`. Only `PUT` was exposed before, so
  neither the re-enrolment sweep nor LGPD art. 18 erasure was reachable from
  the SDK.
  - `GET` reports `expiresAt` / `expired`. The reference image is hard-deleted
    by lifecycle 90 days after enrolment and the record outlives it by a grace
    window *so that* this flag can be found in time. Sweep inside that window:
    once it closes the record goes too and the route answers `404`, which is
    indistinguishable from "never enrolled". Miss it and the expiry surfaces as
    a `422` in the middle of a signature.
  - `DELETE` destroys every stored version of the reference image, not just the
    current one — `versionsDeleted` reports how many.
- **`ENROLLMENT.EXPIRING` / `ENROLLMENT.EXPIRED`** webhook event types.
- **Per-request biometric thresholds** — `policy.minSimilarity` and
  `policy.minLivenessConfidence` let a transaction demand more confidence than
  the account default. They only tighten: a value below the tenant minimum is
  rejected with `400` naming the current floor rather than silently ignored.
  Percentages (`95`) and fractions (`0.95`) both pass through untouched.
- **Advance surface brought in line with the API** — the `confirm_signer` and
  `complete_document_photo` actions, plus `cpfCnpj`, `documentImage`,
  `documentType`, `deviceInfo` and the four sandbox scores
  (`sandboxSimilarity`, `sandboxLivenessConfidence`, `sandboxBrightness`,
  `sandboxSharpness`). The document-photo fallback flow was previously not
  reachable from any SDK.
- **`errorCode` / `errorDetail` / `retryable` / `fallback` on the advance
  response.** This is the one to read if you integrate biometrics: a rejected
  step returns **200** with the session still `ACTIVE` and the reason in the
  body, not as an HTTP error. Code that only branches on the status — or only
  catches exceptions — reads a rejection as a success. Emitted today:
  `BIOMETRIC_MATCH_FAILED`, `LIVENESS_NOT_COMPLETED`, `DOCUMENT_QUALITY_LOW`,
  `DOCUMENT_MATCH_FAILED` and the `SERPRO_*` family.
- **`referenceImage` on session creation** — a per-transaction reference face,
  which allows signing without a prior enrolment.

## [1.10.0] - 2026-08-20

### Added

- **`signing_sessions.link(session_id)`** — `POST /v1/signing-sessions/{sessionId}/link`. The endpoint has
  been in the API and documented in the OpenAPI spec all along, but no SDK in any
  language exposed it, so there was no supported way to recover a signing link
  once the create response was gone.
  - A signing link is single-use: after the signer finishes — or the embed token
    is otherwise consumed — reopening the same URL returns
    `401 Embed token has been consumed`. This mints a new one **without creating
    another transaction and without consuming quota**.
  - Works for standalone and envelope sessions alike.
  - The session must be `ACTIVE`. A completed or cancelled one returns 409: a
    link to a finished session would authenticate nothing. Reach the signed
    document through the envelope's combined stamp or the transaction download
    instead.
  - `expiresAt` is inherited from the original session and is **not** extended.
  - Sends no idempotency key, deliberately. A retry must mint a fresh URL, not
    replay one that has already been consumed.
  - **Authorises the tenant, not the end user.** The API cannot tell which of
    your users is entitled to a given link, so an application whose users share
    one tenant has to establish that itself before calling — otherwise this is a
    way for one user to obtain another's signing credential.
- `MintSigningLinkResponse` model (`session_id`, `transaction_id`, `url`, `expires_at`, `expires_in`).

### Fixed

- **The `User-Agent` reported a version nobody was running.** 1.9.0 shipped reporting `signdocs-brasil-python/1.8.0`, and `__version__` said 1.8.0 while `pyproject.toml` said 1.9.0 — three sources for one number, none compared. The version
  constant now moves with the package, and a test compares it against
  `pyproject.toml` so a release that forgets it fails instead of shipping.

## [1.9.0] - 2026-08-20

### Changed

- **`envelopes.add_session()` and `verification.verify_document()` accept
  `idempotency_key`** and route through the idempotent request path, matching
  `envelopes.create()`. Keyword-only, so no existing call breaks.

### Fixed

- **`add_session` retried without an idempotency key.** The client retries
  `{429, 500, 503}`, and this call sent no key — so a 500 became a second
  signer, a second quota charge and a second invitation, while `create()` was
  already keyed. Pass a **distinct key per signer**: the API scopes its cache by
  key and resolved path, and all signers on an envelope share that path, so one
  key returns signer 1's response — and clientSecret — for signer 2.

- **`verify_document` charged the verification quota on every retry.** The
  endpoint is metered and its answer is a pure function of the PDF, so a retry
  paid twice for an identical result.

## [1.8.0] - 2026-07-30

### Added

- **Envelope cancellation** — `POST /v1/envelopes/{envelopeId}/cancel` has existed since envelopes shipped and is what the Telegram bot calls, but no SDK exposed it. Consumers were left cancelling each member session by hand, which is not the same operation: it leaves the envelope's own status ACTIVE (verified against HML — an envelope whose sessions are every one CANCELLED still reports ACTIVE), costs a call per signer, and records N separate cancellations instead of one auditable terminal event.
  - Transitions every non-terminal session and its transaction to CANCELLED, then marks the envelope CANCELLED.
  - Signatures already collected are preserved and reported as `preservedSignedCount` — cancelling stops the pending signers, it never invalidates evidence already gathered.
  - Idempotent: re-cancelling returns `cancelledCount` 0 and `alreadyCancelled` true.
  - Optional `reason` is recorded in the audit trail; the API defaults it to `envelope_cancelled`.
  - Shipped in lockstep with signdocs-brasil-php 1.9.0.

### Changed

- `User-Agent` bumped to `signdocs-brasil-python/1.8.0`.

## [1.7.0] - 2026-07-29

### Added

- **`signatureUrl` and `documentFormat` on the download response.** `GET /v1/transactions/{id}/download` has always returned these for non-PDF transactions, but the model parsed only `originalUrl` / `signedUrl` and silently dropped them — so there was no way to reach a detached CAdES signature through the SDK at all. Verified against HML: the API returns six fields where the model exposed four.
  - `documentFormat` is `'pdf'` or `'generic'`, derived by the API from the uploaded bytes (not the filename).
  - `signatureUrl` is the presigned URL for the detached `.p7s`, returned **instead of** `signedUrl` when `documentFormat` is `'generic'` — a non-PDF cannot carry an embedded signature.
  - Caveat worth knowing when consuming it: the API presigns that S3 key without checking that the object exists, so a non-PDF signed under a click/OTP policy still comes back with a `signatureUrl` — one that 404s on GET, because only the digital-certificate step writes a `.p7s`. Branch on the signing policy, not on the field being set.
  - Shipped in lockstep with signdocs-brasil-php 1.8.0.

## [1.6.1] - 2026-06-25

### Changed

- API-documentation link in README now points to https://docs.signdocs.com.br
  (was a dead relative path).

## [1.6.0] - 2026-06-25

### Added

- `client.verification.verify_document(request)` — detects whether a PDF
  already carries signatures via `POST /v1/verify/document`. Unlike the other
  verification methods, this endpoint is **authenticated**: it requires a
  Bearer token with the `verification:write` scope and runs only against
  **production credentials**.
- New models backing the endpoint:
  - `VerifyDocumentRequest` — `{content, filename?}` where `content` is the
    base64-encoded PDF.
  - `VerifyDocumentResponse` — `{signed, signature_count, signatures,
    checked_at}`.
  - `DetectedSignature` — `{method, type, confidence, sub_filter?, filter?}`
    where `type` is one of `"pades"`, `"pkcs7"`, `"legacy"`, or
    `"digital_certificate"`.

## [1.5.0] - 2026-04-27

### Added

- `envelope_id: str | None` on `VerificationResponse` — populated when the
  verified evidence belongs to a multi-signer envelope. Use it to drill
  back up to the envelope via
  `client.verification.verify_envelope(envelope_id)`. Omitted for
  standalone signing-session evidences.
- Three new webhook event types on `WebhookEventType`:
  - `ENVELOPE.CREATED` — emitted when a multi-signer envelope is created.
  - `ENVELOPE.ALL_SIGNED` — emitted when every signer has completed.
  - `ENVELOPE.EXPIRED` — emitted when an envelope expires with one or
    more pending signatures.

### Changed

- `User-Agent` bumped to `signdocs-brasil-python/1.5.0`.

## [1.4.1] - 2026-04-27

### Fixed

- `WebhookTestResponse` shape now matches the API spec. Previously the model
  declared `{delivery_id, status, status_code}` reading from
  `data["deliveryId"]`/`["status"]`/`["statusCode"]`, but
  `POST /v1/webhooks/{id}/test` actually returns
  `{webhookId, testDelivery: {httpStatus, success, error?, timestamp}}`. The
  typed wrapper was returning all-empty fields against the live HML API.
  `WebhookTestResponse` is now `{webhook_id, test_delivery}` where
  `test_delivery` is a new `WebhookTestDelivery` dataclass with
  `http_status`, `success`, `timestamp`, and optional `error`. Both classes
  serialize to and deserialize from the camelCase API field names but expose
  Python snake_case attributes.

### Changed

- `User-Agent` bumped to `signdocs-brasil-python/1.4.1`.

## [1.4.0] - 2026-04-23

### Added

- `Owner` dataclass — optional requester identity (`email`, `name`) on `CreateSigningSessionRequest` and `CreateEnvelopeRequest`. When provided, SignDocs automatically emails each signer an invitation with their signing URL (when `signer.email` differs from `owner.email`, case-insensitive) and emails the owner a completion notification per signer completion (plus a final "all signed" message for envelopes). Omit `owner` to keep the traditional behavior.
- `invite_sent` field on `SigningSession` and `EnvelopeSession` response models. Populated by the API when an invitation email was dispatched.

### Changed

- `User-Agent` bumped to `signdocs-brasil-python/1.4.0`.

## [1.3.0] - 2026-04-20

### Fixed

- `webhooks.list()` now correctly returns `list[Webhook]` instead of iterating over the raw API envelope's dict keys. Previously the method silently returned garbage (`Webhook.from_dict("webhooks")`, `Webhook.from_dict("count")`). The method now reads the envelope's `webhooks` field, and accepts a bare list defensively for test fixtures.

### Added

- `signdocs_brasil.TokenCache` — pluggable OAuth token cache (abstract base class). Inject via `ClientConfig(token_cache=my_cache)` to share tokens across serverless workers or short-lived processes. Default `InMemoryTokenCache` preserves pre-1.3 single-process behavior.
- `signdocs_brasil.CachedToken` frozen dataclass and `signdocs_brasil.InMemoryTokenCache` default implementation (thread-safe via `threading.Lock`).
- `signdocs_brasil.ResponseMetadata` — captures `RateLimit-*`, `Deprecation`, `Sunset`, and request-ID headers from every API response. Register an observer via `ClientConfig(on_response=lambda m: ...)`. Parses RFC 8594 `Deprecation`/`Sunset` headers in both IMF-fixdate and `@<unix-seconds>` forms.
- Webhook event types for the NT65 INSS consignado flow:
  - `STEP.PURPOSE_DISCLOSURE_SENT` — purpose-disclosure notification delivered to the beneficiary
  - `TRANSACTION.DEADLINE_APPROACHING` — ≤2 business days remaining until the INSS submission deadline
- `signdocs_brasil.models.webhook.NT65_EVENTS` — frozenset of NT65 event names for compliance-gated filtering.
- `SIGNING_SESSION.CREATED`, `SIGNING_SESSION.COMPLETED`, `SIGNING_SESSION.CANCELLED`, `SIGNING_SESSION.EXPIRED` added to the `WebhookEventType` literal (aligning with the OpenAPI spec's 17 canonical events; these were emitted by the API but not modeled by the SDK).

### Changed

- `AuthHandler.__init__` accepts an optional `cache: TokenCache`. Cache keys are derived deterministically from `client_id + base_url + scopes` (SHA-256 truncated to 32 hex chars) so the same credentials reuse the same cached token across process boundaries. The client_id is never present in plaintext in the key.
- `AuthHandler.invalidate()` now deletes the cache entry instead of clearing an internal field.
- SDK `User-Agent` bumped to `signdocs-brasil-python/1.3.0`.

### Deprecated

- None.

### Fixed

- None.

## [1.2.0] - 2026-04-14

### Added

- `client.verification.verify_envelope(envelope_id)` — public resource method for the new `GET /v1/verify/envelope/{envelopeId}` endpoint. Returns envelope status, signers list (each with `evidence_id` for drill-down via `verification.verify()`), and consolidated download URLs.
- `EnvelopeVerificationResponse`, `EnvelopeVerificationSigner`, `EnvelopeVerificationDownloads`, and `VerificationDownloadItem` models. For non-PDF envelopes signed with digital certificates, `downloads.consolidated_signature` exposes a single PKCS#7 / CMS detached `.p7s` containing every signer's `SignerInfo`. For PDF envelopes, `downloads.combined_signed_pdf` exposes the merged PDF.
- `VerificationSigner.cpf_cnpj` and `VerificationResponse.tenant_cnpj` fields (previously returned by the API but not modeled by the SDK).
- `VerificationDownloads.original_document` and `signed_signature` fields (previously undocumented), matching the real shape the API returns.

### Changed

- `VerificationDownloads.signed_signature` is now `None` when the evidence belongs to a multi-signer envelope (the API omits the field). For standalone signing sessions (single-signer non-PDF with digital certificate) the field is still populated. To retrieve the consolidated `.p7s` for an envelope, use `client.verification.verify_envelope()` instead.

### Removed

- `VerificationDownloads.signed_pdf` — the field was modeled by the SDK but never actually returned by the API. No real-world consumer could have depended on it.

## [1.1.0] - 2026-03-27

### Added

- Signing sessions resource (`client.signing_sessions`): create, get_status, cancel, list, wait_for_completion
- Envelopes resource (`client.envelopes`): create, get, add_session, combined_stamp — multi-signer workflows with parallel or sequential signing
- Per-request timeout on all resource methods via `timeout` keyword argument
- Custom `requests.Session` injection via `ClientConfig.session`
- Request/response logging via `ClientConfig.logger`
- New models: signing session types, envelope types, Geolocation, PurposeDisclosureResult, SerproIdentityResult, DocumentPhotoMatchResult
- New step types: SERPRO_IDENTITY_CHECK, DOCUMENT_PHOTO_MATCH, PURPOSE_DISCLOSURE
- New policy profiles: BIOMETRIC_SERPRO, BIOMETRIC_DOCUMENT_FALLBACK

## [1.0.0] - 2026-03-02

### Added

- Full API coverage: transactions, documents, steps, signing, evidence, verification, users, webhooks, document groups, health
- OAuth2 `client_credentials` authentication with client secret
- Private Key JWT (ES256) authentication with `client_assertion`
- Automatic token caching with 30-second refresh buffer
- Thread-safe token refresh
- Auto-pagination via `list_auto_paginate()` iterator on transactions
- Exponential backoff retry with jitter (429, 500, 503)
- Retry-After header support
- Idempotency keys (auto-generated UUID) on POST requests
- Typed exceptions for all HTTP error codes (RFC 7807 Problem Details)
- Webhook signature verification (HMAC-SHA256, constant-time comparison)
- Configurable base URL, timeout, max retries, and scopes
- Clean top-level exports: `from signdocs_brasil import SignDocsBrasilClient, ClientConfig`
- Full model exports: `from signdocs_brasil.models import *`
- Python 3.9 through 3.13 support

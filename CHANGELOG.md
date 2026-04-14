# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

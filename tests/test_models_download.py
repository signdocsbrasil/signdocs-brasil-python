"""Detached-signature fields on DownloadResponse (non-PDF transactions)."""

from signdocs_brasil.models.document import DownloadResponse


def test_download_response_parses_detached_signature_fields() -> None:
    # Non-PDF transactions come back as documentFormat 'generic' with a
    # detached CAdES signature instead of an embedded signedUrl.
    resp = DownloadResponse.from_dict(
        {
            "transactionId": "tx_2",
            "expiresIn": 900,
            "documentFormat": "generic",
            "originalUrl": "https://s3.example.com/document.docx",
            "signatureUrl": "https://s3.example.com/signature.p7s",
        }
    )

    assert resp.document_format == "generic"
    assert resp.signature_url == "https://s3.example.com/signature.p7s"
    assert resp.signed_url is None


def test_download_response_leaves_new_fields_none_for_a_pdf() -> None:
    resp = DownloadResponse.from_dict(
        {
            "transactionId": "tx_1",
            "expiresIn": 900,
            "documentFormat": "pdf",
            "signedUrl": "https://s3.example.com/signed.pdf",
        }
    )

    assert resp.signature_url is None
    assert resp.signed_url == "https://s3.example.com/signed.pdf"
    assert resp.document_format == "pdf"

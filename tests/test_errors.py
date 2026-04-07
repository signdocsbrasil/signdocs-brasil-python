"""Tests for the error hierarchy and parse_api_error."""

import pytest

from signdocs_brasil.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    ProblemDetail,
    RateLimitError,
    ServiceUnavailableError,
    SignDocsBrasilApiError,
    UnauthorizedError,
    UnprocessableEntityError,
    parse_api_error,
)


class TestProblemDetail:
    def test_from_dict_basic(self):
        pd = ProblemDetail.from_dict({
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "detail": "Invalid input",
        })
        assert pd.type == "about:blank"
        assert pd.title == "Bad Request"
        assert pd.status == 400
        assert pd.detail == "Invalid input"

    def test_from_dict_with_extra_fields(self):
        pd = ProblemDetail.from_dict({
            "type": "about:blank",
            "title": "Bad Request",
            "status": 400,
            "custom_field": "custom_value",
            "errors": [{"field": "name"}],
        })
        assert pd.extra["custom_field"] == "custom_value"
        assert pd.extra["errors"] == [{"field": "name"}]

    def test_from_dict_missing_optional_fields(self):
        pd = ProblemDetail.from_dict({"type": "about:blank", "title": "Error", "status": 500})
        assert pd.detail is None
        assert pd.instance is None


class TestParseApiError:
    @pytest.mark.parametrize(
        "status,expected_class",
        [
            (400, BadRequestError),
            (401, UnauthorizedError),
            (403, ForbiddenError),
            (404, NotFoundError),
            (409, ConflictError),
            (422, UnprocessableEntityError),
            (429, RateLimitError),
            (500, InternalServerError),
            (503, ServiceUnavailableError),
        ],
    )
    def test_status_code_mapping(self, status, expected_class):
        body = {"type": "about:blank", "title": f"HTTP {status}", "status": status}
        error = parse_api_error(status, body)
        assert isinstance(error, expected_class)
        assert error.status == status

    def test_unknown_status_returns_base_api_error(self):
        error = parse_api_error(418, {"type": "about:blank", "title": "Teapot", "status": 418})
        assert isinstance(error, SignDocsBrasilApiError)
        assert error.status == 418

    def test_rate_limit_error_retry_after(self):
        error = parse_api_error(
            429,
            {"type": "about:blank", "title": "Rate Limited", "status": 429},
            retry_after=5,
        )
        assert isinstance(error, RateLimitError)
        assert error.retry_after_seconds == 5

    def test_non_rfc7807_body_string(self):
        error = parse_api_error(500, "Internal Server Error")
        assert isinstance(error, InternalServerError)
        assert error.detail == "Internal Server Error"
        assert "signdocs.com.br/errors/500" in error.type

    def test_non_rfc7807_body_dict_without_type(self):
        error = parse_api_error(400, {"message": "bad input"})
        assert isinstance(error, BadRequestError)
        assert "signdocs.com.br/errors/400" in error.type

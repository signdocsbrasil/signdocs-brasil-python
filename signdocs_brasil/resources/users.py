"""Users resource for biometric enrollment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.user import EnrollUserRequest, EnrollUserResponse

if TYPE_CHECKING:
    from .._http_client import HttpClient


class UsersResource:
    """User management operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def enroll(
        self,
        user_external_id: str,
        request: EnrollUserRequest,
        *,
        timeout: int | None = None,
    ) -> EnrollUserResponse:
        """Enroll a user with a biometric reference image.

        Args:
            user_external_id: The external user identifier.
            request: Enrollment data including the reference image.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnrollUserResponse with enrollment confirmation.
        """
        data = self._http.request(
            "PUT",
            f"/v1/users/{user_external_id}/enrollment",
            body=request.to_dict(),
            timeout=timeout,
        )
        return EnrollUserResponse.from_dict(data)

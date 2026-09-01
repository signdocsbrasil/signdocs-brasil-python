"""Users resource for biometric enrollment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.user import (
    DeleteEnrollmentResponse,
    EnrollmentStatusResponse,
    EnrollUserRequest,
    EnrollUserResponse,
)

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

    def get_enrollment(
        self,
        user_external_id: str,
        *,
        timeout: int | None = None,
    ) -> EnrollmentStatusResponse:
        """Read whether a user is enrolled and, crucially, until when.

        Use it to sweep your user base and re-enrol before ``expired`` flips.
        Nothing warns you on its own beyond the ``ENROLLMENT.EXPIRING``
        webhook, and once the grace window closes this raises NotFound rather
        than reporting an expired enrolment.

        Args:
            user_external_id: The external user identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnrollmentStatusResponse with the expiry window.
        """
        data = self._http.request(
            "GET",
            f"/v1/users/{user_external_id}/enrollment",
            timeout=timeout,
        )
        return EnrollmentStatusResponse.from_dict(data)

    def delete_enrollment(
        self,
        user_external_id: str,
        *,
        timeout: int | None = None,
    ) -> DeleteEnrollmentResponse:
        """Erase a user's biometric enrolment (LGPD art. 18).

        Destroys every stored version of the reference image, not just the
        current one, and removes the record. Irreversible.

        Args:
            user_external_id: The external user identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            DeleteEnrollmentResponse with what was destroyed.
        """
        data = self._http.request(
            "DELETE",
            f"/v1/users/{user_external_id}/enrollment",
            timeout=timeout,
        )
        return DeleteEnrollmentResponse.from_dict(data)

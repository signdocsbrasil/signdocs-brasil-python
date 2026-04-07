"""Transaction resource for creating, listing, and managing transactions."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from ..models.transaction import (
    CancelTransactionResponse,
    CreateTransactionRequest,
    FinalizeResponse,
    Transaction,
    TransactionListParams,
    TransactionListResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class TransactionsResource:
    """Transaction CRUD and lifecycle operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        request: CreateTransactionRequest,
        idempotency_key: str | None = None,
        *,
        timeout: int | None = None,
    ) -> Transaction:
        """Create a new transaction.

        Automatically generates an X-Idempotency-Key header if one is not provided.

        Args:
            request: Transaction creation parameters.
            idempotency_key: Optional explicit idempotency key (UUID4 generated if omitted).
            timeout: Per-request timeout in milliseconds.

        Returns:
            The created Transaction.
        """
        data = self._http.request_with_idempotency(
            "POST",
            "/v1/transactions",
            body=request.to_dict(),
            idempotency_key=idempotency_key,
            timeout=timeout,
        )
        return Transaction.from_dict(data)

    def list(
        self,
        params: TransactionListParams | None = None,
        *,
        timeout: int | None = None,
    ) -> TransactionListResponse:
        """List transactions with optional filters and pagination.

        Args:
            params: Optional filter/pagination parameters.
            timeout: Per-request timeout in milliseconds.

        Returns:
            Paginated TransactionListResponse.
        """
        query = params.to_query() if params else None
        data = self._http.request("GET", "/v1/transactions", query=query, timeout=timeout)
        return TransactionListResponse.from_dict(data)

    def get(self, transaction_id: str, *, timeout: int | None = None) -> Transaction:
        """Get a transaction by ID.

        Args:
            transaction_id: The transaction identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            The Transaction.
        """
        data = self._http.request(
            "GET", f"/v1/transactions/{transaction_id}", timeout=timeout,
        )
        return Transaction.from_dict(data)

    def cancel(
        self, transaction_id: str, *, timeout: int | None = None,
    ) -> CancelTransactionResponse:
        """Cancel a transaction.

        Args:
            transaction_id: The transaction identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            CancelTransactionResponse with cancellation details.
        """
        data = self._http.request(
            "DELETE", f"/v1/transactions/{transaction_id}", timeout=timeout,
        )
        return CancelTransactionResponse.from_dict(data)

    def finalize(self, transaction_id: str, *, timeout: int | None = None) -> FinalizeResponse:
        """Finalize a transaction after all steps are complete.

        Args:
            transaction_id: The transaction identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            FinalizeResponse with evidence details.
        """
        data = self._http.request(
            "POST", f"/v1/transactions/{transaction_id}/finalize", timeout=timeout,
        )
        return FinalizeResponse.from_dict(data)

    def list_auto_paginate(
        self,
        params: TransactionListParams | None = None,
        *,
        timeout: int | None = None,
    ) -> Iterator[Transaction]:
        """Iterate through all transactions, automatically fetching subsequent pages.

        Args:
            params: Optional filter parameters (next_token is managed automatically).
            timeout: Per-request timeout in milliseconds.

        Yields:
            Individual Transaction objects across all pages.
        """
        list_params = TransactionListParams(
            status=params.status if params else None,
            user_external_id=params.user_external_id if params else None,
            document_group_id=params.document_group_id if params else None,
            limit=params.limit if params else None,
            start_date=params.start_date if params else None,
            end_date=params.end_date if params else None,
        )

        while True:
            response = self.list(list_params, timeout=timeout)
            yield from response.transactions
            if not response.next_token:
                break
            list_params.next_token = response.next_token

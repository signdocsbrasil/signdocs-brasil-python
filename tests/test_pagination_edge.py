"""Phase 6: Pagination edge case tests for the Python SDK."""
from unittest.mock import MagicMock

from signdocs_brasil._http_client import HttpClient
from signdocs_brasil.models.transaction import TransactionListParams
from signdocs_brasil.resources.transactions import TransactionsResource


def mock_http():
    return MagicMock(spec=HttpClient)


def make_tx(tx_id="tx_1", status="COMPLETED"):
    return {
        "tenantId": "ten_1",
        "transactionId": tx_id,
        "status": status,
        "purpose": "DOCUMENT_SIGNATURE",
        "policy": {"profile": "CLICK_ONLY"},
        "signer": {"name": "Test", "userExternalId": "ext_1"},
        "steps": [],
        "expiresAt": "2024-12-31T23:59:59Z",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }


class TestListPagination:
    def test_empty_first_page(self):
        http = mock_http()
        http.request.return_value = {"transactions": [], "count": 0}
        tx = TransactionsResource(http)

        resp = tx.list()

        assert resp.transactions == []
        assert resp.count == 0
        assert resp.next_token is None

    def test_single_page_no_next_token(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx("tx_1"), make_tx("tx_2")],
            "count": 2,
        }
        tx = TransactionsResource(http)

        resp = tx.list()

        assert len(resp.transactions) == 2
        assert resp.count == 2
        assert resp.next_token is None
        assert resp.transactions[0].transaction_id == "tx_1"
        assert resp.transactions[1].transaction_id == "tx_2"

    def test_forward_next_token(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx("tx_3")],
            "count": 1,
            "nextToken": "page3",
        }
        tx = TransactionsResource(http)

        params = TransactionListParams(next_token="page2")
        resp = tx.list(params)

        assert resp.next_token == "page3"
        http.request.assert_called_once()
        call_kwargs = http.request.call_args
        assert "page2" in str(call_kwargs)

    def test_limit_one_returns_single_item(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx("tx_1")],
            "count": 1,
            "nextToken": "next",
        }
        tx = TransactionsResource(http)

        params = TransactionListParams(limit=1)
        resp = tx.list(params)

        assert len(resp.transactions) == 1
        assert resp.next_token == "next"

    def test_max_limit_100(self):
        http = mock_http()
        items = [make_tx(f"tx_{i}") for i in range(100)]
        http.request.return_value = {
            "transactions": items,
            "count": 100,
            "nextToken": "more",
        }
        tx = TransactionsResource(http)

        params = TransactionListParams(limit=100)
        resp = tx.list(params)

        assert len(resp.transactions) == 100
        assert resp.next_token == "more"

    def test_next_token_null_means_end(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx("tx_last")],
            "count": 1,
            "nextToken": None,
        }
        tx = TransactionsResource(http)

        resp = tx.list()

        assert resp.next_token is None


class TestAutoPaginate:
    def test_single_page_iterates_and_stops(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx("tx_1"), make_tx("tx_2")],
            "count": 2,
        }
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 2
        assert http.request.call_count == 1

    def test_multi_page_iteration(self):
        http = mock_http()
        http.request.side_effect = [
            {
                "transactions": [make_tx("tx_1"), make_tx("tx_2")],
                "count": 2,
                "nextToken": "page2",
            },
            {
                "transactions": [make_tx("tx_3")],
                "count": 1,
            },
        ]
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 3
        assert http.request.call_count == 2
        assert items[0].transaction_id == "tx_1"
        assert items[2].transaction_id == "tx_3"

    def test_empty_result_set(self):
        http = mock_http()
        http.request.return_value = {"transactions": [], "count": 0}
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 0
        assert http.request.call_count == 1

    def test_filters_propagated_across_pages(self):
        http = mock_http()
        http.request.side_effect = [
            {
                "transactions": [make_tx("tx_1")],
                "count": 1,
                "nextToken": "page2",
            },
            {
                "transactions": [make_tx("tx_2")],
                "count": 1,
            },
        ]
        tx = TransactionsResource(http)

        params = TransactionListParams(status="COMPLETED")
        items = list(tx.list_auto_paginate(params))

        assert len(items) == 2
        assert http.request.call_count == 2

    def test_three_pages(self):
        http = mock_http()
        http.request.side_effect = [
            {
                "transactions": [make_tx("tx_1")],
                "count": 1,
                "nextToken": "p2",
            },
            {
                "transactions": [make_tx("tx_2")],
                "count": 1,
                "nextToken": "p3",
            },
            {
                "transactions": [make_tx("tx_3")],
                "count": 1,
            },
        ]
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 3
        assert http.request.call_count == 3

    def test_page_with_empty_items_terminates(self):
        http = mock_http()
        http.request.side_effect = [
            {
                "transactions": [make_tx("tx_1")],
                "count": 1,
                "nextToken": "page2",
            },
            {
                "transactions": [],
                "count": 0,
            },
        ]
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 1
        assert http.request.call_count == 2

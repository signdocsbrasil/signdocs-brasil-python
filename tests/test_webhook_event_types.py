"""Lockstep assertions between the SDK's WebhookEventType literal and the OpenAPI spec."""

from __future__ import annotations

from pathlib import Path
from typing import get_args

import pytest

from signdocs_brasil.models.webhook import NT65_EVENTS, WebhookEventType

# Canonical list from openapi/openapi.yaml (see line ~2473). The SDK's literal
# MUST stay in lockstep with this set; if this assertion fails, either the SDK
# needs to be updated or the spec has drifted.
CANONICAL_EVENTS: frozenset[str] = frozenset(
    {
        "TRANSACTION.CREATED",
        "TRANSACTION.COMPLETED",
        "TRANSACTION.CANCELLED",
        "TRANSACTION.FAILED",
        "TRANSACTION.EXPIRED",
        "TRANSACTION.FALLBACK",
        "TRANSACTION.DEADLINE_APPROACHING",
        "STEP.STARTED",
        "STEP.COMPLETED",
        "STEP.FAILED",
        "STEP.PURPOSE_DISCLOSURE_SENT",
        "QUOTA.WARNING",
        "API.DEPRECATION_NOTICE",
        "SIGNING_SESSION.CREATED",
        "SIGNING_SESSION.COMPLETED",
        "SIGNING_SESSION.CANCELLED",
        "SIGNING_SESSION.EXPIRED",
    }
)


class TestWebhookEventTypeLockstep:
    def test_exactly_17_events(self):
        assert len(CANONICAL_EVENTS) == 17

    def test_literal_contains_all_canonical_events(self):
        literal_values = frozenset(get_args(WebhookEventType))
        missing = CANONICAL_EVENTS - literal_values
        extra = literal_values - CANONICAL_EVENTS
        assert not missing, f"SDK missing canonical events: {sorted(missing)}"
        assert not extra, f"SDK has non-spec events: {sorted(extra)}"

    def test_nt65_events_are_correct(self):
        assert NT65_EVENTS == frozenset(
            {"TRANSACTION.DEADLINE_APPROACHING", "STEP.PURPOSE_DISCLOSURE_SENT"}
        )

    def test_nt65_events_are_subset_of_canonical(self):
        assert NT65_EVENTS.issubset(CANONICAL_EVENTS)


class TestAgainstOpenApiSpec:
    """Optional assertion against the actual openapi.yaml if reachable."""

    @pytest.mark.skipif(
        not (
            Path(__file__).resolve().parents[3]
            / "openapi"
            / "openapi.yaml"
        ).exists(),
        reason="openapi.yaml not reachable from this checkout",
    )
    def test_canonical_matches_openapi_file(self):
        spec_path = (
            Path(__file__).resolve().parents[3] / "openapi" / "openapi.yaml"
        )
        content = spec_path.read_text(encoding="utf-8")

        # Locate the WebhookEventType enum block and parse the enum values.
        marker = "WebhookEventType:"
        idx = content.find(marker)
        assert idx >= 0, "Could not locate WebhookEventType in openapi.yaml"

        # Read forward until we find "enum:" then the list of `- VALUE` lines.
        tail = content[idx:]
        enum_idx = tail.find("enum:")
        assert enum_idx >= 0
        enum_block = tail[enum_idx + len("enum:") :]

        spec_events: set[str] = set()
        for line in enum_block.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                value = stripped[2:].strip()
                # Only event-name-shaped strings (uppercase, dotted).
                if value and value[0].isupper() and "." in value:
                    spec_events.add(value)
            elif stripped and not stripped.startswith("- ") and not stripped.startswith("#"):
                # First non-enum-item line ends the block (e.g. next key).
                if not stripped.startswith(("x-", "-")):
                    break

        assert spec_events == CANONICAL_EVENTS, (
            "OpenAPI spec has drifted from CANONICAL_EVENTS: "
            f"missing_from_canonical={sorted(spec_events - CANONICAL_EVENTS)} "
            f"missing_from_spec={sorted(CANONICAL_EVENTS - spec_events)}"
        )

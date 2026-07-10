from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ingest.contracts.models import BatchIdentity
from ingest.observability.signals import SignalCollector


def build_manifest(
    *,
    schema_version: str,
    dataset_version: str,
    identity: BatchIdentity,
    signals: SignalCollector,
    row_counts: dict[str, int],
    rules_applied: list[str],
    exclusions: dict[str, int],
    publish_status: str,
    holdout_eligible: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "dataset_version": dataset_version,
        "source_hash": identity.source_hash,
        "batch_id": identity.batch_id,
        "rules_applied": rules_applied,
        "row_counts": row_counts,
        "exclusions": exclusions,
        "warning_codes": [c for c in signals.codes() if c != "INGEST_FILTER_INFO"],
        "publish_status": publish_status,
        "holdout_eligible": holdout_eligible,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def dataset_version_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

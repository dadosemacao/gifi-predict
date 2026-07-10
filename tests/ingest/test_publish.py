from __future__ import annotations

import json

import pandas as pd

from ingest.contracts.models import PublishBlockedError
from ingest.observability.signals import Severity, SignalCollector
from ingest.publish.publisher import publish_batch_artifacts


def test_atomic_publish_and_current_pointer(settings) -> None:
    l2 = settings.l2_path
    l2.mkdir(parents=True, exist_ok=True)
    signals = SignalCollector()
    df = pd.DataFrame({"data_processo": ["2024-01-01"], "turno": [1], "x": [1.0]})
    manifest = {
        "schema_version": settings.schema_version,
        "dataset_version": "2026-07-10T00:00:00Z",
        "publish_status": "published_ok",
    }
    publish_batch_artifacts(
        l2,
        "2026-07-10T00:00:00Z",
        {"train_features": df, "holdout_features": df.iloc[0:0]},
        manifest,
        signals,
        settings.schema_version,
    )
    current = json.loads((l2 / "current.json").read_text(encoding="utf-8"))
    assert current["schema_version"] == settings.schema_version


def test_publish_blocked_on_signal(settings) -> None:
    signals = SignalCollector()
    signals.emit("INGEST_MIX_FAIL", Severity.BLOCKING, "bad mix")
    try:
        publish_batch_artifacts(
            settings.l2_path,
            "v1",
            {"train_features": pd.DataFrame({"a": [1]})},
            {"publish_status": "published_ok"},
            signals,
            settings.schema_version,
        )
        raise AssertionError("expected PublishBlockedError")
    except PublishBlockedError:
        pass

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ingest.contracts.models import PublishBlockedError, PublishConflictError
from ingest.observability.signals import SignalCollector
from ingest.publish.atomic_io import atomic_write_json
from ingest.publish.parquet_writer import write_parquet


def publish_batch_artifacts(
    l2_root: Path,
    version: str,
    artifacts: dict[str, pd.DataFrame],
    manifest: dict[str, Any],
    signals: SignalCollector,
    schema_version: str,
) -> Path:
    if signals.has_blocking:
        raise PublishBlockedError("blocking signals present")

    final = l2_root / "published" / version
    staging = l2_root / "published" / f".staging_{version}"
    if final.exists():
        raise PublishConflictError(f"version already exists: {version}")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    try:
        for name, frame in artifacts.items():
            dest = staging / f"{name}.parquet"
            write_parquet(frame, dest, schema_version)
            paths[name] = dest
        atomic_write_json(staging / "batch_manifest.json", manifest)
        os.replace(staging, final)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise

    current_pointer = l2_root / "current.json"
    pointer_updated = False
    pointer_skip_reason: str | None = None
    if manifest.get("publish_status") in ("published_ok", "published_with_warnings"):
        if manifest.get("holdout_eligible", True):
            if current_pointer.exists():
                atomic_write_json(
                    l2_root / "current.json.previous",
                    json.loads(current_pointer.read_text(encoding="utf-8")),
                )
            pointer = {
                "dataset_version": version,
                "schema_version": schema_version,
                "paths": {k: str(final / f"{k}.parquet") for k in artifacts},
                "manifest": str(final / "batch_manifest.json"),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            atomic_write_json(current_pointer, pointer)
            pointer_updated = True
        else:
            pointer_skip_reason = "holdout_ineligible_per_warning_matrix"
    manifest_path = final / "batch_manifest.json"
    if manifest_path.exists():
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored["current_pointer_updated"] = pointer_updated
        if pointer_skip_reason:
            stored["current_pointer_skip_reason"] = pointer_skip_reason
        atomic_write_json(manifest_path, stored)
    return final

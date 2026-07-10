from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ingest.observability.signals import SignalCollector


def quarantine_batch(
    l2_root: Path,
    batch_id: str,
    source_path: Path,
    signals: SignalCollector,
    sample_violations: list[dict[str, Any]] | None = None,
) -> Path:
    target = l2_root / "quarantine" / batch_id
    target.mkdir(parents=True, exist_ok=True)
    meta = {
        "batch_id": batch_id,
        "source_path": str(source_path),
        "signals": signals.codes(),
        "sample_violations": sample_violations or [],
    }
    (target / "quarantine_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if source_path.exists() and source_path.is_file():
        shutil.copy2(source_path, target / source_path.name)
    return target

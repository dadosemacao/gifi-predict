from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def log_event(payload: dict[str, Any], sink: Path | None = None) -> None:
    line = json.dumps(payload, ensure_ascii=False)
    print(line, file=sys.stdout)
    if sink is not None:
        sink.parent.mkdir(parents=True, exist_ok=True)
        with sink.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def log_simulate_start(
    *,
    run_id: str,
    component: str,
    l2_dataset_version: str = "",
    l2_source_hash: str = "",
    log_file: Path | None = None,
) -> None:
    log_event(
        {
            "timestamp": _now_iso(),
            "level": "INFO",
            "event": "simulate_start",
            "run_id": run_id,
            "component": component,
            "l2_dataset_version": l2_dataset_version,
            "l2_source_hash": l2_source_hash,
        },
        log_file,
    )


def log_simulate_end(
    *,
    run_id: str,
    component: str,
    duration_ms: int,
    mae_tsa_cascade: float | None = None,
    families_selected: dict[str, str] | None = None,
    release_ok: bool | None = None,
    log_file: Path | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": _now_iso(),
        "level": "INFO",
        "event": "simulate_end",
        "run_id": run_id,
        "component": component,
        "duration_ms": duration_ms,
    }
    if mae_tsa_cascade is not None:
        payload["mae_tsa_cascade"] = mae_tsa_cascade
    if families_selected:
        payload["families_selected"] = families_selected
    if release_ok is not None:
        payload["release_ok"] = release_ok
    log_event(payload, log_file)

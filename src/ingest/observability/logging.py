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


def log_ingest_start(
    *,
    path: str,
    batch_id: str,
    component: str,
    source_hash: str = "",
    cenario_id: str | None = None,
    log_file: Path | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": _now_iso(),
        "level": "INFO",
        "event": "ingest_start",
        "path": path,
        "batch_id": batch_id,
        "component": component,
        "source_hash": source_hash,
    }
    if cenario_id:
        payload["cenario_id"] = cenario_id
    log_event(payload, log_file)


def log_ingest_end(
    *,
    path: str,
    batch_id: str,
    component: str,
    duration_ms: int,
    source_hash: str = "",
    rows_read: int = 0,
    rows_written: int = 0,
    rows_excluded: int = 0,
    publish_status: str = "",
    signals: list[str] | None = None,
    schema_version: str = "",
    sla_ms: int | None = None,
    cenario_id: str | None = None,
    reject_reason: str | None = None,
    row_count: int | None = None,
    log_file: Path | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": _now_iso(),
        "level": "INFO",
        "event": "ingest_end",
        "path": path,
        "batch_id": batch_id,
        "component": component,
        "duration_ms": duration_ms,
        "source_hash": source_hash,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "rows_excluded": rows_excluded,
        "publish_status": publish_status,
        "signals": signals or [],
        "schema_version": schema_version,
    }
    if sla_ms is not None:
        payload["sla_ms"] = sla_ms
    if cenario_id:
        payload["cenario_id"] = cenario_id
        payload["template_id"] = "template_cenario_v0"
    if reject_reason:
        payload["reject_reason"] = reject_reason
    if row_count is not None:
        payload["row_count"] = row_count
    log_event(payload, log_file)

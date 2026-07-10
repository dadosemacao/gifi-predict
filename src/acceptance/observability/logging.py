from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def log_accept_event(
    *,
    run_id: str,
    event: str,
    log_file: Path,
    **fields: Any,
) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        "run_id": run_id,
        **fields,
    }
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

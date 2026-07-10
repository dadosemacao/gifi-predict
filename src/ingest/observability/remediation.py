from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def record_remediation(l2_root: Path, record: dict[str, Any]) -> Path:
    remediation_id = record.get("remediation_id") or str(uuid.uuid4())
    record = {
        **record,
        "remediation_id": remediation_id,
        "resolved_at": record.get(
            "resolved_at", datetime.now(UTC).isoformat()
        ),
    }
    out_dir = l2_root / "remediation"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{remediation_id}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

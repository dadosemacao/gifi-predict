from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class ApiCallRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    ts_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    method: str = ""
    path: str = ""
    endpoint: str = ""
    status_code: int = 0
    duration_ms: float = 0.0
    client_ip: str | None = None
    user_agent: str | None = None
    product: str | None = None
    model_id: str | None = None
    family: str | None = None
    run_id: str | None = None
    request_json: str | None = None
    response_json: str | None = None
    field_origins_json: str | None = None
    warnings_json: str | None = None
    metrics_json: str | None = None
    file_sha256: str | None = None
    file_name: str | None = None
    row_count: int | None = None
    mode: str | None = None
    error_detail: str | None = None

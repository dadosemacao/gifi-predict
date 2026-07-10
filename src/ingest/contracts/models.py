from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class BatchIdentity:
    batch_id: str
    source_path: str
    source_hash: str
    period_start: str | None
    period_end: str | None
    ingested_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ArtifactMeta:
    schema_version: str
    dataset_version: str
    source_hash: str
    publish_status: str
    warning_codes: list[str] = field(default_factory=list)


class PublishBlockedError(Exception):
    pass


class PublishConflictError(Exception):
    pass


class SchemaVersionError(Exception):
    pass

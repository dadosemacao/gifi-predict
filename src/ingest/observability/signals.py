from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass
class IngestSignal:
    code: str
    severity: Severity
    message: str
    row_ref: str | None = None


@dataclass
class SignalCollector:
    signals: list[IngestSignal] = field(default_factory=list)

    def emit(
        self,
        code: str,
        severity: Severity,
        message: str,
        row_ref: str | None = None,
    ) -> None:
        self.signals.append(IngestSignal(code, severity, message, row_ref))

    @property
    def has_blocking(self) -> bool:
        return any(s.severity == Severity.BLOCKING for s in self.signals)

    def codes(self) -> list[str]:
        return [s.code for s in self.signals]

    def aggregate_status(self) -> str:
        if self.has_blocking:
            return "ingest_fail"
        if any(s.severity == Severity.WARNING for s in self.signals):
            return "ingest_warn"
        return "ingest_ok"

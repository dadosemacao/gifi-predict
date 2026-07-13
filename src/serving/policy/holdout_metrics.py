from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HoldoutMetrics:
    mae_holdout: float
    r2_holdout: float
    interval_80_coverage: float

    def as_dict(self) -> dict[str, float]:
        return {
            "mae_holdout": self.mae_holdout,
            "r2_holdout": self.r2_holdout,
            "interval_80_coverage": self.interval_80_coverage,
        }


def load_json_pointer(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_holdout_metrics(
    repo_root: Path,
    *,
    run_id: str,
    pointer: dict[str, Any],
    report_path: Path,
    default_interval: float = 0.0,
) -> HoldoutMetrics:
    src = pointer if pointer.get("run_id") == run_id else {}
    holdout = src.get("holdout_metrics") or {}

    if holdout.get("mae") is None or holdout.get("r2") is None:
        report = _load_report_for_run(repo_root / report_path, run_id)
        if report:
            src = report
            holdout = report.get("holdout_metrics") or {}

    mae = holdout.get("mae")
    r2 = holdout.get("r2")
    if mae is None or r2 is None:
        raise ValueError(f"métricas de holdout ausentes para run_id={run_id}")

    interval = src.get("interval_80_coverage")
    if interval is None:
        interval = default_interval

    return HoldoutMetrics(
        mae_holdout=float(mae),
        r2_holdout=float(r2),
        interval_80_coverage=float(interval),
    )


def _load_report_for_run(report_path: Path, run_id: str) -> dict[str, Any]:
    if not report_path.exists():
        return {}
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if data.get("run_id") == run_id:
        return data
    return {}

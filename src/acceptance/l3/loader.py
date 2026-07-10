from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sklearn.pipeline import Pipeline

from simulation.package.publisher import load_candidate_pipes_by_run_id


@dataclass(frozen=True)
class L3CandidateBundle:
    run_id: str
    candidate_dir: Path
    manifest: dict[str, Any]
    metrics: dict[str, Any]
    explainability: dict[str, Any]
    pipes: dict[str, Pipeline]
    feature_cols: dict[str, list[str]]
    champions: dict[str, str]
    pointer: dict[str, Any]


def load_l3_candidate(models_root: Path, run_id: str) -> L3CandidateBundle:
    candidate_dir = models_root / "candidates" / run_id
    if not candidate_dir.is_dir():
        raise FileNotFoundError(f"candidate run not found: {run_id}")

    manifest_path = candidate_dir / "candidate_manifest.json"
    metrics_path = candidate_dir / "metrics_holdout.json"
    explain_path = candidate_dir / "explainability.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"candidate_manifest.json missing for {run_id}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = (
        json.loads(metrics_path.read_text(encoding="utf-8"))
        if metrics_path.exists()
        else {}
    )
    explainability = (
        json.loads(explain_path.read_text(encoding="utf-8"))
        if explain_path.exists()
        else {}
    )

    pipes, feature_cols, pointer = load_candidate_pipes_by_run_id(models_root, run_id)
    champions = manifest.get("champions", pointer.get("champions", {}))

    return L3CandidateBundle(
        run_id=run_id,
        candidate_dir=candidate_dir,
        manifest=manifest,
        metrics=metrics,
        explainability=explainability,
        pipes=pipes,
        feature_cols=feature_cols,
        champions=champions,
        pointer=pointer,
    )

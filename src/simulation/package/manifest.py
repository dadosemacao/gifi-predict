from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sklearn.pipeline import Pipeline


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def build_candidate_manifest(
    *,
    run_id: str,
    l2_dataset_version: str,
    l2_schema_version: str,
    l2_source_hash: str,
    l2_paths: dict[str, str],
    champions: dict[str, str],
    random_state: int,
    exclusions: dict[str, dict[str, int]],
    feature_cols: dict[str, list[str]],
    artifact_paths: dict[str, Path],
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for elo, family in champions.items():
        path = artifact_paths[elo]
        artifacts[f"{elo}_{family}"] = {
            "path": path.name,
            "family": family,
            "sha256": _file_sha256(path),
        }
    return {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "l2": {
            "dataset_version": l2_dataset_version,
            "schema_version": l2_schema_version,
            "source_hash": l2_source_hash,
            "paths": l2_paths,
        },
        "champions": champions,
        "feature_cols": feature_cols,
        "random_state": random_state,
        "exclusions": exclusions,
        "artifacts": artifacts,
    }


def extract_explainability(
    pipes: dict[str, dict[str, Pipeline]],
    champions: dict[str, str],
    feature_cols: dict[str, list[str]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for elo, family in champions.items():
        pipe = pipes[elo][family]
        model = pipe.named_steps.get("model")
        cols = feature_cols.get(elo, [])
        entry: dict[str, Any] = {"family": family, "elo": elo}
        if family == "elasticnet" and hasattr(model, "coef_"):
            entry["coefficients"] = {
                col: float(coef)
                for col, coef in zip(cols, model.coef_, strict=False)
            }
        elif family == "randomforest" and hasattr(model, "feature_importances_"):
            entry["feature_importances"] = {
                col: float(imp)
                for col, imp in zip(cols, model.feature_importances_, strict=False)
            }
        out[elo] = entry
    return out

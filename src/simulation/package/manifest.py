from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
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


def _named_feature_dict(
    values: np.ndarray,
    cols: list[str],
) -> dict[str, float] | None:
    flat = np.asarray(values, dtype=float).ravel()
    if flat.size == 0 or not cols:
        return None
    if flat.size != len(cols):
        return None
    return {col: float(val) for col, val in zip(cols, flat, strict=False)}


def _extract_feature_importances(model: object, cols: list[str]) -> dict[str, float] | None:
    importances: np.ndarray | None = None
    get_importance = getattr(model, "get_feature_importance", None)
    if callable(get_importance):
        importances = np.asarray(get_importance(), dtype=float)
    elif hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_, dtype=float)
    if importances is None:
        return None
    return _named_feature_dict(importances, cols)


def _extract_coefficients(model: object, cols: list[str]) -> dict[str, float] | None:
    if not hasattr(model, "coef_"):
        return None
    return _named_feature_dict(np.asarray(model.coef_, dtype=float), cols)


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

        coefficients = _extract_coefficients(model, cols)
        if coefficients is not None:
            entry["coefficients"] = coefficients
        else:
            importances = _extract_feature_importances(model, cols)
            if importances is not None:
                entry["feature_importances"] = importances

        out[elo] = entry
    return out

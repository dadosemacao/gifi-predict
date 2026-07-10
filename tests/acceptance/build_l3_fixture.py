from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.pipeline import Pipeline

from simulation.features.elo_specs import default_elo_specs
from simulation.package.manifest import build_candidate_manifest, extract_explainability
from simulation.package.publisher import publish_candidate


class MonotonicFormulaRegressor(BaseEstimator, RegressorMixin):
    """Regressor determinístico com direção física para testes de aceite."""

    def fit(self, X, y=None):
        frame = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        self.n_features_in_ = frame.shape[1]
        self.feature_names_in_ = np.asarray(frame.columns, dtype=object)
        return self

    def predict(self, X):
        frame = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        tsa = np.full(len(frame), 3000.0, dtype=float)
        if "TPC" in frame.columns:
            tsa -= 8.0 * pd.to_numeric(frame["TPC"], errors="coerce").fillna(65).to_numpy()
        if "Extrativo_AT" in frame.columns:
            tsa -= 120.0 * pd.to_numeric(
                frame["Extrativo_AT"], errors="coerce"
            ).fillna(2.0).to_numpy()
        if "Carga_Alcalina" in frame.columns:
            tsa -= 80.0 * pd.to_numeric(
                frame["Carga_Alcalina"], errors="coerce"
            ).fillna(19.0).to_numpy()
        if "DB_LAB" in frame.columns:
            tsa -= 0.8 * pd.to_numeric(frame["DB_LAB"], errors="coerce").fillna(480).to_numpy()
        if "VMI" in frame.columns:
            tsa -= 400.0 * pd.to_numeric(frame["VMI"], errors="coerce").fillna(0.25).to_numpy()
        return tsa


def _elo_pipe(cols: list[str]) -> Pipeline:
    return Pipeline([("model", MonotonicFormulaRegressor())])


def build_monotonic_candidate(
    models_root: Path,
    *,
    run_id: str | None = None,
    mae_tsa_cascade: float = 30.0,
) -> str:
    run_id = run_id or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    specs = default_elo_specs()
    feature_cols = {elo: list(specs[elo]["features"]) for elo in specs}
    champions = {"elo1": "baseline", "elo2": "baseline", "elo3": "baseline"}
    pipes = {
        "elo1": _elo_pipe(feature_cols["elo1"]),
        "elo2": _elo_pipe(feature_cols["elo2"]),
        "elo3": _elo_pipe(feature_cols["elo3"]),
    }
    for elo, pipe in pipes.items():
        cols = feature_cols[elo]
        X = pd.DataFrame(np.zeros((4, len(cols))), columns=cols)
        pipe.fit(X, np.full(4, 1200.0))

    metrics = {
        "mae_extrativos": 0.5,
        "mae_carga": 0.5,
        "mae_tsa_isolated": mae_tsa_cascade,
        "mae_tsa_cascade": mae_tsa_cascade,
        "holdout_rows": 10,
    }
    explainability = extract_explainability(
        {elo: {champions[elo]: pipes[elo]} for elo in champions},
        champions,
        feature_cols,
    )
    manifest_base = {
        "run_id": run_id,
        "l2": {
            "dataset_version": "test-mini",
            "schema_version": "1.0.0",
            "source_hash": "sha256:test",
            "paths": {},
        },
        "champions": champions,
        "feature_cols": feature_cols,
        "random_state": 42,
        "exclusions": {},
        "artifacts": {},
    }
    candidate_dir = publish_candidate(
        models_root,
        run_id,
        pipes,
        champions,
        manifest_base,
        metrics,
        explainability,
        release_ok=False,
    )
    artifact_paths = {
        elo: candidate_dir / f"{elo}_{champions[elo]}.joblib" for elo in champions
    }
    final_manifest = build_candidate_manifest(
        run_id=run_id,
        l2_dataset_version="test-mini",
        l2_schema_version="1.0.0",
        l2_source_hash="sha256:test",
        l2_paths={},
        champions=champions,
        random_state=42,
        exclusions={},
        feature_cols=feature_cols,
        artifact_paths=artifact_paths,
    )
    (candidate_dir / "candidate_manifest.json").write_text(
        json.dumps(final_manifest, indent=2), encoding="utf-8"
    )
    return run_id

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from simulation.forecast.features import build_process_row, compute_lags, engineer_features
from simulation.forecast.specs import DEFAULT_ANCHOR, MIN_TSA_HISTORY, PROCESS_FEATURES


@dataclass(frozen=True)
class ForecastArtifact:
    pipe: Pipeline
    anchor: str
    feature_columns: list[str]
    interval_quantiles: dict[str, float]
    family: str = "unknown"
    run_id: str = ""


def load_forecast_artifact(path: Path) -> ForecastArtifact:
    payload = joblib.load(path)
    if isinstance(payload, ForecastArtifact):
        return payload
    if not isinstance(payload, dict) or "pipe" not in payload:
        raise ValueError(f"artefato de forecast inválido: {path}")
    return ForecastArtifact(
        pipe=payload["pipe"],
        anchor=payload.get("anchor", DEFAULT_ANCHOR),
        feature_columns=list(payload.get("feature_columns", [])),
        interval_quantiles=dict(payload.get("interval_quantiles", {})),
        family=str(payload.get("family", "unknown")),
        run_id=str(payload.get("run_id", "")),
    )


def save_forecast_artifact(path: Path, artifact: ForecastArtifact) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipe": artifact.pipe,
            "anchor": artifact.anchor,
            "feature_columns": artifact.feature_columns,
            "interval_quantiles": artifact.interval_quantiles,
            "family": artifact.family,
            "run_id": artifact.run_id,
        },
        path,
    )


def predict_tsa(
    artifact: ForecastArtifact,
    process: dict[str, float],
    tsa_history: list[float],
) -> dict[str, Any]:
    if len(tsa_history) < MIN_TSA_HISTORY:
        raise ValueError(
            f"tsa_history requer ao menos {MIN_TSA_HISTORY} valores; recebeu {len(tsa_history)}"
        )
    for key in PROCESS_FEATURES:
        if key not in process:
            raise ValueError(f"campo de processo ausente: {key}")

    lags = compute_lags(tsa_history)
    frame = build_process_row(process, lags)
    X = engineer_features(frame)
    if artifact.feature_columns:
        missing = [c for c in artifact.feature_columns if c not in X.columns]
        if missing:
            raise ValueError(f"features derivadas ausentes: {missing}")
        X = X[artifact.feature_columns]

    anchor_val = float(frame[artifact.anchor].iloc[0])
    residual = float(artifact.pipe.predict(X)[0])
    tsa_pred = anchor_val + residual

    q_lo = float(artifact.interval_quantiles.get("q_lo", 0.0))
    q_hi = float(artifact.interval_quantiles.get("q_hi", 0.0))

    return {
        "tsa_dia": tsa_pred,
        "tsa_dia_lo": tsa_pred + q_lo,
        "tsa_dia_hi": tsa_pred + q_hi,
        "anchor": anchor_val,
        "anchor_name": artifact.anchor,
        "residual": residual,
        "baselines": {
            "lag1": lags["TSA_lag1"],
            "roll3": lags["TSA_roll3"],
            "roll7": lags["TSA_roll7"],
        },
        "lags": lags,
    }

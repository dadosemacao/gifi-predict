from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.cascade.inference import infer_dataframe
from simulation.features.matrix import build_matrix
from simulation.metrics.stage import mae, rmse, wape


def _per_elo_metrics(
    pipe: Pipeline,
    holdout: pd.DataFrame,
    elo: str,
    specs: dict[str, Any],
) -> dict[str, float]:
    X, y, _, _ = build_matrix(holdout, elo, specs, enforce_min_rows=False)
    preds = pipe.predict(X)
    return {
        "mae": mae(y.to_numpy(), preds),
        "rmse": rmse(y.to_numpy(), preds),
        "wape": wape(y.to_numpy(), preds),
    }


def evaluate_holdout(
    fitted: dict[str, dict[str, Pipeline]],
    champions: dict[str, str],
    holdout: pd.DataFrame,
    specs: dict[str, Any],
    feature_cols: dict[str, list[str]],
    *,
    db_proxy_factor: float = 0.985,
    holdout_elo3: pd.DataFrame | None = None,
    training_mode: str = "cascade",
) -> dict[str, Any]:
    elo3_frame = holdout_elo3 if holdout_elo3 is not None else holdout
    isolated_pipe = fitted["elo3"][champions["elo3"]]
    X_iso, y_iso, _, _ = build_matrix(elo3_frame, "elo3", specs, enforce_min_rows=False)
    iso_preds = isolated_pipe.predict(X_iso)
    mae_isolated = mae(y_iso.to_numpy(), iso_preds)

    if training_mode == "direct_tsa":
        y_tsa = pd.to_numeric(holdout["TSA_dia"], errors="coerce")
        mask = y_tsa.notna()
        return {
            "elo3": {
                "family": champions["elo3"],
                "mae": mae_isolated,
                "rmse": rmse(y_iso.to_numpy(), iso_preds),
                "wape": wape(y_iso.to_numpy(), iso_preds),
            },
            "mae_tsa_isolated": mae_isolated,
            "mae_tsa_cascade": mae_isolated,
            "rmse_tsa_cascade": rmse(y_iso.to_numpy(), iso_preds),
            "wape_tsa_cascade": wape(y_iso.to_numpy(), iso_preds),
            "mae_primary": mae_isolated,
            "mae_metric": "isolated",
            "training_mode": training_mode,
            "holdout_rows": int(mask.sum()),
            "elo3_fit_rows": int(len(X_iso)),
        }

    champion_pipes = {
        elo: fitted[elo][champions[elo]] for elo in ("elo1", "elo2", "elo3")
    }

    per_elo: dict[str, Any] = {}
    for elo in ("elo1", "elo2"):
        per_elo[elo] = {
            "family": champions[elo],
            **_per_elo_metrics(champion_pipes[elo], holdout, elo, specs),
        }
    per_elo["elo3"] = {
        "family": champions["elo3"],
        **_per_elo_metrics(champion_pipes["elo3"], elo3_frame, "elo3", specs),
    }

    cascade_preds = infer_dataframe(
        holdout,
        "A",
        champion_pipes,
        feature_cols,
        db_proxy_factor=db_proxy_factor,
        strict_scenario=False,
    )
    y_tsa = pd.to_numeric(holdout["TSA_dia"], errors="coerce")
    mask = y_tsa.notna()
    y_true = y_tsa[mask].to_numpy()
    y_pred = cascade_preds.loc[mask, "TSA_dia"].to_numpy()

    isolated_pipe = champion_pipes["elo3"]
    _, y_iso, _, _ = build_matrix(elo3_frame, "elo3", specs, enforce_min_rows=False)
    iso_preds = isolated_pipe.predict(
        build_matrix(elo3_frame, "elo3", specs, enforce_min_rows=False)[0]
    )

    return {
        "elo1": per_elo["elo1"],
        "elo2": per_elo["elo2"],
        "elo3": per_elo["elo3"],
        "mae_extrativos": per_elo["elo1"]["mae"],
        "mae_carga": per_elo["elo2"]["mae"],
        "mae_tsa_isolated": mae(y_iso.to_numpy(), iso_preds),
        "mae_tsa_cascade": mae(y_true, y_pred),
        "rmse_tsa_cascade": rmse(y_true, y_pred),
        "wape_tsa_cascade": wape(y_true, y_pred),
        "mae_primary": mae(y_true, y_pred),
        "mae_metric": "cascade",
        "training_mode": training_mode,
        "holdout_rows": int(mask.sum()),
    }

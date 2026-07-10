from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


def pick_elo12_fill_pipes(
    fitted: dict[str, dict[str, Pipeline]],
    families: list[str],
) -> dict[str, Pipeline]:
    chosen: dict[str, Pipeline] = {}
    for elo in ("elo1", "elo2"):
        for family in ("randomforest", "elasticnet", "baseline", *families):
            if family in fitted[elo]:
                chosen[elo] = fitted[elo][family]
                break
        else:
            chosen[elo] = next(iter(fitted[elo].values()))
    return chosen


def _predict_elo_all_rows(
    df: pd.DataFrame,
    elo: str,
    pipe: Pipeline,
    specs: dict[str, Any],
) -> pd.Series:
    spec = specs[elo]
    optional = set(spec.get("optional_features", []))
    cols = [c for c in spec["features"] if c in df.columns or c not in optional]
    X = df[cols].apply(pd.to_numeric, errors="coerce")
    required = [c for c in cols if c not in optional]
    bad = X[required].isna().any(axis=1) if required else pd.Series(False, index=df.index)
    keep = ~bad
    preds = pd.Series(np.nan, index=df.index, dtype=float)
    if keep.any():
        preds.loc[keep] = pipe.predict(X.loc[keep])
    return preds


def enrich_elo3_cascade_features(
    df: pd.DataFrame,
    fitted_elo12: dict[str, Pipeline],
    specs: dict[str, Any],
) -> pd.DataFrame:
    """Fill missing Extrativo_AT / Carga_Alcalina with Modo A cascade predictions."""
    out = df.copy()
    extr_pred = _predict_elo_all_rows(out, "elo1", fitted_elo12["elo1"], specs)
    out["Extrativo_AT"] = out["Extrativo_AT"].where(
        out["Extrativo_AT"].notna(), extr_pred
    )
    carga_pred = _predict_elo_all_rows(out, "elo2", fitted_elo12["elo2"], specs)
    out["Carga_Alcalina"] = out["Carga_Alcalina"].where(
        out["Carga_Alcalina"].notna(), carga_pred
    )
    return out

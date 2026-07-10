from __future__ import annotations

from itertools import product
from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.cascade.inference import infer_dataframe
from simulation.features.matrix import build_matrix
from simulation.metrics.stage import mae


def _candidate_families(
    family_pipes: dict[str, Pipeline],
    families: list[str] | None,
) -> list[str]:
    candidates = list(family_pipes.keys())
    if families:
        candidates = [f for f in candidates if f in families] or candidates
    return candidates


def select_champions(
    fitted: dict[str, dict[str, Pipeline]],
    holdout: pd.DataFrame,
    specs: dict[str, Any],
    families: list[str] | None = None,
    *,
    feature_cols: dict[str, list[str]] | None = None,
    db_proxy_factor: float = 0.985,
    select_by_cascade: bool = False,
    elo3_families: tuple[str, ...] | None = None,
) -> dict[str, str]:
    if select_by_cascade and feature_cols is not None:
        return _select_by_cascade(
            fitted,
            holdout,
            feature_cols,
            families=families,
            db_proxy_factor=db_proxy_factor,
            elo3_families=elo3_families,
        )

    champions: dict[str, str] = {}
    for elo, family_pipes in fitted.items():
        X, y, _, _ = build_matrix(holdout, elo, specs, enforce_min_rows=False)
        candidates = _candidate_families(family_pipes, families)
        best_family = candidates[0]
        best_mae = float("inf")
        for family in candidates:
            pipe = family_pipes[family]
            preds = pipe.predict(X)
            score = mae(y.to_numpy(), preds)
            if score < best_mae:
                best_mae = score
                best_family = family
        champions[elo] = best_family
    return champions


def _select_by_cascade(
    fitted: dict[str, dict[str, Pipeline]],
    holdout: pd.DataFrame,
    feature_cols: dict[str, list[str]],
    *,
    families: list[str] | None,
    db_proxy_factor: float,
    elo3_families: tuple[str, ...] | None,
) -> dict[str, str]:
    y_tsa = pd.to_numeric(holdout["TSA_dia"], errors="coerce")
    mask = y_tsa.notna()
    y_true = y_tsa[mask].to_numpy()

    elo1_candidates = _candidate_families(fitted["elo1"], families)
    elo2_candidates = _candidate_families(fitted["elo2"], families)
    if elo3_families:
        elo3_candidates = [f for f in elo3_families if f in fitted["elo3"]]
    else:
        elo3_candidates = _candidate_families(fitted["elo3"], families)

    best_combo = (elo1_candidates[0], elo2_candidates[0], elo3_candidates[0])
    best_mae = float("inf")
    for f1, f2, f3 in product(elo1_candidates, elo2_candidates, elo3_candidates):
        pipes = {
            "elo1": fitted["elo1"][f1],
            "elo2": fitted["elo2"][f2],
            "elo3": fitted["elo3"][f3],
        }
        preds = infer_dataframe(
            holdout,
            "A",
            pipes,
            feature_cols,
            db_proxy_factor=db_proxy_factor,
            strict_scenario=False,
        )
        score = mae(y_true, preds.loc[mask, "TSA_dia"].to_numpy())
        if score < best_mae:
            best_mae = score
            best_combo = (f1, f2, f3)

    return {"elo1": best_combo[0], "elo2": best_combo[1], "elo3": best_combo[2]}

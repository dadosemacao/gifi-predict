from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline

from simulation.exceptions import TrainingDataError
from simulation.features.matrix import build_matrix
from simulation.models.cascade_training import _predict_elo_all_rows
from simulation.models.families import make_family


def enrich_elo3_oof_features(
    df: pd.DataFrame,
    specs: dict[str, Any],
    *,
    random_state: int,
    cv_folds: int,
    min_train_rows: int,
    elo1_family: str = "randomforest",
    elo2_family: str = "randomforest",
    fallback_elo12: dict[str, Pipeline] | None = None,
    date_col: str = "data_processo",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Stack Elo 1/2 with temporal OOF predictions to expand Elo 3 training rows."""
    if date_col in df.columns:
        ordered = df.sort_values(date_col).reset_index(drop=True)
    else:
        ordered = df.reset_index(drop=True)

    n = len(ordered)
    oof_extr = pd.Series(np.nan, index=ordered.index, dtype=float)
    oof_carga = pd.Series(np.nan, index=ordered.index, dtype=float)

    n_splits = min(cv_folds, max(2, n // max(min_train_rows * 2, 1)))
    tss = TimeSeriesSplit(n_splits=n_splits)
    folds_run = 0

    for train_idx, val_idx in tss.split(ordered):
        fold_train = ordered.iloc[train_idx]
        fold_val = ordered.iloc[val_idx]

        try:
            X1, y1, _, _ = build_matrix(
                fold_train,
                "elo1",
                specs,
                min_rows=min_train_rows,
                enforce_min_rows=True,
            )
        except TrainingDataError:
            continue

        pipe1 = make_family(elo1_family, random_state)
        pipe1.fit(X1, y1)
        extr_oof = _predict_elo_all_rows(fold_val, "elo1", pipe1, specs)
        oof_extr.iloc[val_idx] = extr_oof.to_numpy()

        train_st = fold_train.copy()
        extr_train = _predict_elo_all_rows(train_st, "elo1", pipe1, specs)
        train_st["Extrativo_AT"] = train_st["Extrativo_AT"].where(
            train_st["Extrativo_AT"].notna(), extr_train
        )

        try:
            X2, y2, _, _ = build_matrix(
                train_st,
                "elo2",
                specs,
                min_rows=min_train_rows,
                enforce_min_rows=True,
            )
        except TrainingDataError:
            continue

        pipe2 = make_family(elo2_family, random_state)
        pipe2.fit(X2, y2)

        val_st = fold_val.copy()
        val_st["Extrativo_AT"] = val_st["Extrativo_AT"].where(
            val_st["Extrativo_AT"].notna(), extr_oof
        )
        carga_oof = _predict_elo_all_rows(val_st, "elo2", pipe2, specs)
        oof_carga.iloc[val_idx] = carga_oof.to_numpy()
        folds_run += 1

    out = ordered.copy()
    fallback_extr_rows = 0
    fallback_carga_rows = 0

    if fallback_elo12 is not None:
        need_extr = oof_extr.isna()
        if need_extr.any():
            fb_extr = _predict_elo_all_rows(out, "elo1", fallback_elo12["elo1"], specs)
            oof_extr = oof_extr.where(oof_extr.notna(), fb_extr)
            fallback_extr_rows = int(need_extr.sum())

        need_carga = oof_carga.isna()
        if need_carga.any():
            carga_base = out.copy()
            carga_base["Extrativo_AT"] = out["Extrativo_AT"].where(
                out["Extrativo_AT"].notna(), oof_extr
            )
            fb_carga = _predict_elo_all_rows(
                carga_base, "elo2", fallback_elo12["elo2"], specs
            )
            oof_carga = oof_carga.where(oof_carga.notna(), fb_carga)
            fallback_carga_rows = int(need_carga.sum())

    out["Extrativo_AT"] = out["Extrativo_AT"].where(out["Extrativo_AT"].notna(), oof_extr)
    out["Carga_Alcalina"] = out["Carga_Alcalina"].where(
        out["Carga_Alcalina"].notna(), oof_carga
    )

    meta = {
        "oof_folds": n_splits,
        "folds_run": folds_run,
        "oof_extr_rows": int(oof_extr.notna().sum()),
        "oof_carga_rows": int(oof_carga.notna().sum()),
        "fallback_extr_rows": fallback_extr_rows,
        "fallback_carga_rows": fallback_carga_rows,
        "elo1_family": elo1_family,
        "elo2_family": elo2_family,
    }
    return out, meta

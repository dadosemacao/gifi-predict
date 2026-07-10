from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from simulation.features.matrix import build_matrix
from simulation.models.cascade_training import (
    enrich_elo3_cascade_features,
    pick_elo12_fill_pipes,
)
from simulation.models.families import make_family
from simulation.models.grid_search import TuningConfig, fit_elo3_with_grid_search
from simulation.models.oof_stack import enrich_elo3_oof_features
from simulation.models.split import merge_train_holdout, temporal_train_test_split


ELO_ORDER = ("elo1", "elo2", "elo3")


def _needs_imputer(elo: str, feature_cols: list[str], specs: dict[str, Any]) -> bool:
    optional = set(specs.get(elo, {}).get("optional_features", []))
    return bool(optional & set(feature_cols))


def _elo3_search_and_fit_pools(
    train: pd.DataFrame,
    holdout: pd.DataFrame | None,
    config: TuningConfig,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if holdout is None:
        return train, None
    combined = merge_train_holdout(train, holdout)
    if config.grid_search_pool == "combined_80_20":
        search_df, _ = temporal_train_test_split(combined, train_fraction=config.train_fraction)
        return search_df, combined
    return train, combined


def _elo3_final_fit_pool(
    train: pd.DataFrame,
    holdout: pd.DataFrame | None,
    combined: pd.DataFrame | None,
    config: TuningConfig,
) -> pd.DataFrame:
    if config.training_pool == "combined" and combined is not None:
        return combined
    if config.training_pool == "combined_80_20" and combined is not None:
        fit_df, _ = temporal_train_test_split(combined, train_fraction=config.train_fraction)
        return fit_df
    return train


def _prepare_elo3_frame(
    df: pd.DataFrame,
    specs: dict[str, Any],
    fitted_elo12: dict[str, Pipeline] | None,
    tuning: TuningConfig,
    *,
    random_state: int,
    min_train_rows: int,
) -> tuple[pd.DataFrame, dict[str, Any] | None]:
    if tuning.elo3_oof_stack and fitted_elo12 is not None:
        enriched, meta = enrich_elo3_oof_features(
            df,
            specs,
            random_state=random_state,
            cv_folds=tuning.cv_folds,
            min_train_rows=min_train_rows,
            fallback_elo12=fitted_elo12,
        )
        return enriched, meta
    if tuning.elo3_cascade_fill and fitted_elo12 is not None:
        return enrich_elo3_cascade_features(df, fitted_elo12, specs), None
    return df, None


def train_all(
    train: pd.DataFrame,
    specs: dict[str, Any],
    families: list[str],
    random_state: int,
    *,
    min_train_rows: int = 50,
    holdout: pd.DataFrame | None = None,
    tuning: TuningConfig | None = None,
) -> tuple[
    dict[str, dict[str, Pipeline]],
    dict[str, dict[str, int]],
    dict[str, list[str]],
    dict[str, Any],
]:
    fitted: dict[str, dict[str, Pipeline]] = {elo: {} for elo in ELO_ORDER}
    exclusions: dict[str, dict[str, int]] = {}
    feature_cols: dict[str, list[str]] = {}
    tuning_meta: dict[str, Any] = {"elo3": {}}

    for elo in ("elo1", "elo2"):
        X, y, excl, cols = build_matrix(
            train, elo, specs, min_rows=min_train_rows, enforce_min_rows=True
        )
        exclusions[elo] = excl
        feature_cols[elo] = cols
        impute = _needs_imputer(elo, cols, specs)
        for family in families:
            pipe = make_family(family, random_state, impute_optional=impute)
            pipe.fit(X, y)
            fitted[elo][family] = pipe

    X_ref, y_ref, excl3, cols3 = build_matrix(
        train, "elo3", specs, min_rows=min_train_rows, enforce_min_rows=True
    )
    exclusions["elo3"] = excl3
    feature_cols["elo3"] = cols3
    impute3 = _needs_imputer("elo3", cols3, specs)

    if tuning and tuning.enabled:
        fitted_elo12 = pick_elo12_fill_pipes(fitted, families)

        search_df, combined = _elo3_search_and_fit_pools(train, holdout, tuning)
        search_df, oof_meta_search = _prepare_elo3_frame(
            search_df,
            specs,
            fitted_elo12,
            tuning,
            random_state=random_state,
            min_train_rows=min_train_rows,
        )
        X_search, y_search, _, _ = build_matrix(
            search_df, "elo3", specs, min_rows=min_train_rows, enforce_min_rows=True
        )
        final_pool = _elo3_final_fit_pool(train, holdout, combined, tuning)
        final_pool, oof_meta_final = _prepare_elo3_frame(
            final_pool,
            specs,
            fitted_elo12,
            tuning,
            random_state=random_state,
            min_train_rows=min_train_rows,
        )
        X_final, y_final, _, _ = build_matrix(
            final_pool, "elo3", specs, min_rows=min_train_rows, enforce_min_rows=True
        )
        tuning_meta["elo3"]["grid_search_pool"] = tuning.grid_search_pool
        tuning_meta["elo3"]["training_pool"] = tuning.training_pool
        tuning_meta["elo3"]["cascade_fill"] = tuning.elo3_cascade_fill
        tuning_meta["elo3"]["oof_stack"] = tuning.elo3_oof_stack
        if oof_meta_search:
            tuning_meta["elo3"]["oof_search"] = oof_meta_search
        if oof_meta_final:
            tuning_meta["elo3"]["oof_final"] = oof_meta_final
        tuning_meta["elo3"]["search_rows"] = int(len(X_search))
        tuning_meta["elo3"]["final_fit_rows"] = int(len(X_final))

        for family in tuning.elo3_families:
            try:
                best_pipe, meta = fit_elo3_with_grid_search(
                    X_search,
                    y_search,
                    family,
                    random_state,
                    tuning,
                    impute_optional=impute3,
                )
            except Exception as exc:  # noqa: BLE001 — registrar falha por família
                tuning_meta["elo3"][family] = {
                    "family": family,
                    "error": str(exc),
                }
                continue
            best_pipe.fit(X_final, y_final)
            fitted["elo3"][family] = best_pipe
            tuning_meta["elo3"][family] = meta

        for family in families:
            if family in fitted["elo3"]:
                continue
            pipe = make_family(family, random_state, impute_optional=impute3)
            pipe.fit(X_final, y_final)
            fitted["elo3"][family] = pipe
    else:
        for family in families:
            pipe = make_family(family, random_state, impute_optional=impute3)
            pipe.fit(X_ref, y_ref)
            fitted["elo3"][family] = pipe

    return fitted, exclusions, feature_cols, tuning_meta

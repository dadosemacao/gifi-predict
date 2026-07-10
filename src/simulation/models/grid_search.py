from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline

from simulation.models.families import make_family


@dataclass(frozen=True)
class TuningConfig:
    enabled: bool = True
    cv_folds: int = 5
    elo3_families: tuple[str, ...] = (
        "elasticnet",
        "ridge",
        "lasso",
        "randomforest",
        "extratrees",
        "histgradientboosting",
        "xgboost",
        "lightgbm",
        "catboost",
    )
    grid_search_pool: str = "train"
    training_pool: str = "train"
    train_fraction: float = 0.8
    fast: bool = False
    elo3_cascade_fill: bool = False
    elo3_oof_stack: bool = True
    n_jobs: int = -1
    select_by_cascade: bool = True


def _param_grid(family: str, *, fast: bool) -> dict[str, list[Any]]:
    if family == "elasticnet":
        if fast:
            return {"model__alpha": [0.08], "model__l1_ratio": [0.5]}
        return {
            "model__alpha": [0.01, 0.05, 0.08, 0.2, 0.5, 1.0],
            "model__l1_ratio": [0.2, 0.5, 0.8, 0.95],
        }
    if family == "ridge":
        if fast:
            return {"model__alpha": [1.0]}
        return {"model__alpha": [0.1, 1.0, 10.0, 100.0]}
    if family == "lasso":
        if fast:
            return {"model__alpha": [0.1]}
        return {"model__alpha": [0.01, 0.1, 1.0, 10.0]}
    if family == "randomforest":
        if fast:
            return {"model__n_estimators": [50], "model__min_samples_leaf": [5]}
        return {
            "model__n_estimators": [200, 400, 600],
            "model__min_samples_leaf": [2, 5, 10],
            "model__max_depth": [None, 12, 20],
            "model__max_features": ["sqrt", 0.7],
        }
    if family == "extratrees":
        if fast:
            return {"model__n_estimators": [100], "model__min_samples_leaf": [5]}
        return {
            "model__n_estimators": [200, 400, 600],
            "model__min_samples_leaf": [2, 5, 10],
            "model__max_depth": [None, 12, 20],
            "model__max_features": ["sqrt", 0.7],
        }
    if family == "histgradientboosting":
        if fast:
            return {"model__max_iter": [100], "model__learning_rate": [0.1]}
        return {
            "model__max_iter": [200, 400, 600],
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__max_depth": [4, 6, 10],
            "model__min_samples_leaf": [10, 20, 40],
            "model__l2_regularization": [0.0, 0.1, 1.0],
        }
    if family == "xgboost":
        if fast:
            return {"model__n_estimators": [100], "model__learning_rate": [0.1]}
        return {
            "model__n_estimators": [200, 400, 600],
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__max_depth": [4, 6, 10],
            "model__min_child_weight": [1, 5, 10],
            "model__subsample": [0.8, 1.0],
        }
    if family == "lightgbm":
        if fast:
            return {"model__n_estimators": [100], "model__learning_rate": [0.1]}
        return {
            "model__n_estimators": [200, 400, 600],
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__max_depth": [4, 6, 10],
            "model__num_leaves": [31, 63],
            "model__min_child_samples": [10, 20, 40],
        }
    if family == "catboost":
        if fast:
            return {"model__iterations": [100], "model__learning_rate": [0.1]}
        return {
            "model__iterations": [200, 400, 600],
            "model__learning_rate": [0.03, 0.05, 0.1],
            "model__depth": [4, 6, 10],
            "model__l2_leaf_reg": [1.0, 3.0, 10.0],
        }
    raise ValueError(f"no grid for family: {family}")


def _base_pipeline(family: str, random_state: int, *, impute_optional: bool) -> Pipeline:
    if family == "histgradientboosting":
        steps: list[tuple[str, object]] = []
        if impute_optional:
            from sklearn.impute import SimpleImputer

            steps.append(("imputer", SimpleImputer(strategy="median")))
        steps.append(
            (
                "model",
                HistGradientBoostingRegressor(
                    random_state=random_state,
                    early_stopping=False,
                ),
            )
        )
        return Pipeline(steps)
    return make_family(family, random_state, impute_optional=impute_optional)


def fit_elo3_with_grid_search(
    X_search: pd.DataFrame,
    y_search: pd.Series,
    family: str,
    random_state: int,
    config: TuningConfig,
    *,
    impute_optional: bool,
) -> tuple[Pipeline, dict[str, Any]]:
    pipe = _base_pipeline(family, random_state, impute_optional=impute_optional)
    n_splits = min(config.cv_folds, max(2, len(X_search) // 50))
    cv = TimeSeriesSplit(n_splits=n_splits)
    grid = GridSearchCV(
        pipe,
        _param_grid(family, fast=config.fast),
        cv=cv,
        scoring="neg_mean_absolute_error",
        n_jobs=config.n_jobs,
        refit=True,
        error_score="raise",
    )
    grid.fit(X_search, y_search)
    meta = {
        "family": family,
        "best_params": grid.best_params_,
        "cv_mae": float(-grid.best_score_),
        "cv_folds": n_splits,
    }
    return grid.best_estimator_, meta

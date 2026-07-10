from __future__ import annotations

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _optional_imputer(impute_optional: bool) -> list[tuple[str, object]]:
    if impute_optional:
        return [("imputer", SimpleImputer(strategy="median"))]
    return []


def make_family(name: str, random_state: int, *, impute_optional: bool = False) -> Pipeline:
    steps: list[tuple[str, object]] = list(_optional_imputer(impute_optional))

    if name == "baseline":
        steps.append(("model", DummyRegressor(strategy="mean")))
        return Pipeline(steps)

    if name == "elasticnet":
        steps.append(("scaler", StandardScaler()))
        steps.append(
            (
                "model",
                ElasticNet(
                    alpha=0.08,
                    l1_ratio=0.5,
                    random_state=random_state,
                    max_iter=5000,
                ),
            )
        )
        return Pipeline(steps)

    if name == "ridge":
        steps.append(("scaler", StandardScaler()))
        steps.append(("model", Ridge(alpha=1.0, random_state=random_state)))
        return Pipeline(steps)

    if name == "lasso":
        steps.append(("scaler", StandardScaler()))
        steps.append(
            ("model", Lasso(alpha=0.1, random_state=random_state, max_iter=5000))
        )
        return Pipeline(steps)

    if name == "randomforest":
        steps.append(
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    min_samples_leaf=5,
                    random_state=random_state,
                    n_jobs=1,
                ),
            )
        )
        return Pipeline(steps)

    if name == "extratrees":
        steps.append(
            (
                "model",
                ExtraTreesRegressor(
                    n_estimators=300,
                    min_samples_leaf=5,
                    random_state=random_state,
                    n_jobs=1,
                ),
            )
        )
        return Pipeline(steps)

    if name == "xgboost":
        from xgboost import XGBRegressor

        steps.append(
            (
                "model",
                XGBRegressor(
                    n_estimators=300,
                    learning_rate=0.05,
                    max_depth=6,
                    random_state=random_state,
                    n_jobs=1,
                    verbosity=0,
                ),
            )
        )
        return Pipeline(steps)

    if name == "lightgbm":
        from lightgbm import LGBMRegressor

        steps.append(
            (
                "model",
                LGBMRegressor(
                    n_estimators=300,
                    learning_rate=0.05,
                    max_depth=6,
                    random_state=random_state,
                    n_jobs=1,
                    verbose=-1,
                ),
            )
        )
        return Pipeline(steps)

    if name == "catboost":
        from catboost import CatBoostRegressor

        steps.append(
            (
                "model",
                CatBoostRegressor(
                    iterations=300,
                    learning_rate=0.05,
                    depth=6,
                    random_seed=random_state,
                    verbose=False,
                ),
            )
        )
        return Pipeline(steps)

    raise ValueError(f"unknown family: {name}")

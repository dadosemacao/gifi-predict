from __future__ import annotations

from typing import Any

import pandas as pd

from simulation.exceptions import TrainingDataError


def build_matrix(
    df: pd.DataFrame,
    elo: str,
    specs: dict[str, Any],
    *,
    min_rows: int = 50,
    enforce_min_rows: bool = True,
) -> tuple[pd.DataFrame, pd.Series, dict[str, int], list[str]]:
    if elo not in specs:
        raise ValueError(f"unknown elo: {elo}")
    spec = specs[elo]
    target = spec["target"]
    if target not in df.columns:
        raise ValueError(f"target column missing for {elo}: {target}")

    y = pd.to_numeric(df[target], errors="coerce")
    mask = y.notna()
    exclusions: dict[str, int] = {"na_target": int((~mask).sum())}

    optional = set(spec.get("optional_features", []))
    cols = [c for c in spec["features"] if c in df.columns or c not in optional]
    missing_required = [c for c in spec["features"] if c not in df.columns and c not in optional]
    if missing_required:
        raise ValueError(f"required features missing for {elo}: {missing_required}")

    X = df.loc[mask, cols].apply(pd.to_numeric, errors="coerce")
    required = [c for c in cols if c not in optional]
    bad = X[required].isna().any(axis=1) if required else pd.Series(False, index=X.index)
    exclusions["na_feature"] = int(bad.sum())
    keep = ~bad
    X = X.loc[keep]
    y = y.loc[mask][keep]

    if enforce_min_rows and len(X) < min_rows:
        raise TrainingDataError(
            f"{elo}: only {len(X)} rows after cleaning; minimum is {min_rows}"
        )

    return X, y, exclusions, list(X.columns)

from __future__ import annotations

from typing import Any

import pandas as pd

from simulation.exceptions import TrainingDataError


def _resolve_columns(
    df: pd.DataFrame,
    feature_names: list[str],
    aliases: dict[str, str] | None,
) -> list[str]:
    resolved: list[str] = []
    for name in feature_names:
        if name in df.columns:
            resolved.append(name)
            continue
        alt = (aliases or {}).get(name)
        if alt and alt in df.columns:
            resolved.append(alt)
            continue
        resolved.append(name)
    return resolved


def _encode_categoricals(
    frame: pd.DataFrame,
    cols: list[str],
    categorical: set[str],
    aliases: dict[str, str] | None,
) -> pd.DataFrame:
    out = frame.copy()
    alias_to_canonical = {v: k for k, v in (aliases or {}).items()}
    for col in cols:
        canonical = alias_to_canonical.get(col, col)
        if canonical not in categorical and col not in categorical:
            continue
        series = out[col]
        if not pd.api.types.is_numeric_dtype(series):
            codes, _ = pd.factorize(series.astype(str), sort=True)
            out[col] = codes.astype(float)
        else:
            out[col] = pd.to_numeric(series, errors="coerce")
    return out


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
    aliases = spec.get("column_aliases") or {}
    logical_features = list(spec["features"])
    resolved_names = _resolve_columns(df, logical_features, aliases)

    cols: list[str] = []
    for logical, physical in zip(logical_features, resolved_names, strict=True):
        if physical in df.columns:
            cols.append(physical)
        elif logical not in optional:
            cols.append(physical)

    missing_required = [
        logical
        for logical, physical in zip(logical_features, resolved_names, strict=True)
        if logical not in optional and physical not in df.columns
    ]
    if missing_required:
        raise ValueError(f"required features missing for {elo}: {missing_required}")

    categorical = set(spec.get("categorical_features", []))
    cat_physical: set[str] = set()
    for name in categorical:
        cat_physical.add(name)
        alt = aliases.get(name)
        if alt:
            cat_physical.add(alt)

    subset = df.loc[mask, cols].copy()
    subset = _encode_categoricals(subset, cols, cat_physical, aliases)

    X = subset.apply(pd.to_numeric, errors="coerce")
    required_cols: list[str] = []
    for logical, physical in zip(logical_features, resolved_names, strict=True):
        if logical in optional:
            continue
        if physical in cols:
            required_cols.append(physical)

    bad = X[required_cols].isna().any(axis=1) if required_cols else pd.Series(False, index=X.index)
    exclusions["na_feature"] = int(bad.sum())
    keep = ~bad
    X = X.loc[keep]
    y = y.loc[mask][keep]

    if enforce_min_rows and len(X) < min_rows:
        raise TrainingDataError(
            f"{elo}: only {len(X)} rows after cleaning; minimum is {min_rows}"
        )

    return X, y, exclusions, list(X.columns)

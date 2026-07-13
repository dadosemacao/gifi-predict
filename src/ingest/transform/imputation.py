from __future__ import annotations

from typing import Any

import pandas as pd

from ingest.config import IngestSettings
from ingest.observability.signals import Severity, SignalCollector

# Features do Elo 1 (mix de madeira + idade) usadas para estimar Extrativo_AT.
# Mantido self-contained no Ingest para não depender da Camada 3 (Simulação).
EXTR_IMPUTE_FEATURES: tuple[str, ...] = (
    "pct_A",
    "pct_B",
    "pct_C",
    "pct_D",
    "pct_MG",
    "pct_ABC",
    "pct_CDMG",
    "mix_entropy",
    "mix_hhi",
    "dom_A",
    "dom_B",
    "dom_C",
    "dom_D",
    "dom_MG",
    "Idade",
)


def impute_db_lab(
    df: pd.DataFrame, settings: IngestSettings, signals: SignalCollector
) -> pd.DataFrame:
    out = df.copy()
    if "DB_SGF" not in out.columns:
        return out
    if "DB_LAB" not in out.columns:
        out["DB_LAB"] = pd.NA
    if "db_origin" not in out.columns:
        out["db_origin"] = pd.NA

    proxy_mask = out["DB_LAB"].isna() & out["DB_SGF"].notna()
    if proxy_mask.any():
        out.loc[proxy_mask, "DB_LAB"] = out.loc[proxy_mask, "DB_SGF"] * settings.db_proxy_factor
        out.loc[proxy_mask, "db_origin"] = "proxy"
        signals.emit(
            "INGEST_PROXY_DB",
            Severity.WARNING,
            f"DB_LAB imputed for {int(proxy_mask.sum())} rows",
        )

    lab_mask = out["DB_LAB"].notna() & out["db_origin"].isna()
    out.loc[lab_mask, "db_origin"] = "lab"
    return out


def _available_extr_features(df: pd.DataFrame) -> list[str]:
    return [c for c in EXTR_IMPUTE_FEATURES if c in df.columns]


def fit_extrativo_imputer(
    df: pd.DataFrame,
    *,
    random_state: int = 42,
    min_train_rows: int = 200,
) -> tuple[Any, dict[str, Any]] | None:
    """Treina RandomForest para estimar Extrativo_AT a partir de mix + idade.

    Usa apenas linhas com Extrativo_AT medido e features completas. Retorna
    ``None`` quando não há amostra suficiente (deixa a coluna como NA).
    """
    if "Extrativo_AT" not in df.columns:
        return None
    features = _available_extr_features(df)
    if not features:
        return None

    y = pd.to_numeric(df["Extrativo_AT"], errors="coerce")
    x = df[features].apply(pd.to_numeric, errors="coerce")
    mask = y.notna() & x.notna().all(axis=1)
    if int(mask.sum()) < min_train_rows:
        return None

    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=1,
    )
    model.fit(x.loc[mask, features], y.loc[mask])
    meta = {
        "features": features,
        "n_train_rows": int(mask.sum()),
        "y_min": float(y.loc[mask].min()),
        "y_max": float(y.loc[mask].max()),
    }
    return model, meta


def apply_extrativo_imputer(
    df: pd.DataFrame,
    model: Any,
    meta: dict[str, Any],
    *,
    range_min: float,
    range_max: float,
) -> tuple[pd.DataFrame, int]:
    """Preenche Extrativo_AT ausente com predições do imputer e marca origem."""
    out = df.copy()
    if "extr_origin" not in out.columns:
        out["extr_origin"] = pd.NA

    extr = pd.to_numeric(out["Extrativo_AT"], errors="coerce")
    measured = extr.notna() & out["extr_origin"].isna()
    out.loc[measured, "extr_origin"] = "medido"

    features = meta["features"]
    x = out[features].apply(pd.to_numeric, errors="coerce")
    target = extr.isna() & x.notna().all(axis=1)
    n_estimated = int(target.sum())
    if n_estimated:
        preds = model.predict(x.loc[target, features])
        lo = max(range_min, meta.get("y_min", range_min))
        hi = min(range_max, meta.get("y_max", range_max))
        preds = preds.clip(lo, hi)
        out.loc[target, "Extrativo_AT"] = preds
        out.loc[target, "extr_origin"] = "estimado"
    return out, n_estimated


def impute_extrativo_at(
    df: pd.DataFrame,
    settings: IngestSettings,
    signals: SignalCollector,
) -> pd.DataFrame:
    """Estima Extrativo_AT ausente (Elo 1) dentro do batch histórico.

    Treina o imputer apenas na janela de treino (``data_processo`` <=
    ``train_cutoff``) para não vazar o holdout, e aplica a todas as linhas com
    Extrativo_AT ausente e features de mix completas.
    """
    out = df.copy()
    if "Extrativo_AT" not in out.columns:
        return out
    if "extr_origin" not in out.columns:
        out["extr_origin"] = pd.NA

    extr = pd.to_numeric(out["Extrativo_AT"], errors="coerce")
    out.loc[extr.notna() & out["extr_origin"].isna(), "extr_origin"] = "medido"

    if not settings.extr_impute_enabled:
        return out

    fit_frame = out
    if "data_processo" in out.columns:
        cutoff = pd.to_datetime(settings.train_cutoff, errors="coerce")
        dates = pd.to_datetime(out["data_processo"], errors="coerce")
        train_window = out.loc[dates <= cutoff] if pd.notna(cutoff) else out
        if len(train_window) >= settings.extr_impute_min_train_rows:
            fit_frame = train_window

    fitted = fit_extrativo_imputer(
        fit_frame,
        random_state=settings.extr_impute_random_state,
        min_train_rows=settings.extr_impute_min_train_rows,
    )
    if fitted is None:
        signals.emit(
            "INGEST_SPARSE_LAB",
            Severity.WARNING,
            "Extrativo_AT sem cobertura suficiente para imputação (Elo 1)",
        )
        return out

    model, meta = fitted
    out, n_estimated = apply_extrativo_imputer(
        out,
        model,
        meta,
        range_min=settings.extr_range_min,
        range_max=settings.extr_range_max,
    )
    if n_estimated:
        signals.emit(
            "INGEST_PROXY_EXTR",
            Severity.WARNING,
            f"Extrativo_AT estimated (Elo 1) for {n_estimated} rows",
        )
    return out

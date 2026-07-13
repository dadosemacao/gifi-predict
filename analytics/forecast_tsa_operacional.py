"""Forecast operacional de TSA_dia (Produto A).

Autor: Emerson Antônio
Data: 2026-07-13

Previsão do próximo turno usando:
- features de processo (primeira_base)
- histórico recente de TSA (lag1, roll3, roll7)
- modelo residual em torno de roll3 (baseline temporal)

Pipeline:
1. Baselines (média, lag1, roll3, roll7)
2. Compara famílias ML no resíduo (TimeSeriesSplit)
3. GridSearch no campeão
4. Intervalo empírico 80% (resíduos OOF)
5. Gráfico real vs predito + faixa

Uso:
    PYTHONPATH=src python analytics/forecast_tsa_operacional.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from simulation.models.families import make_family
from simulation.models.grid_search import (
    TuningConfig,
    _base_pipeline,
    fit_elo3_with_grid_search,
)

TARGET = "TSA_dia"
ANCHOR = "TSA_roll3"
PROCESS_FEATURES = [
    "Carga_Alcalina",
    "Kappa",
    "DB_SGF",
    "DB_LAB",
    "Secura_pct",
    "Casca_pct",
    "Extrativo_Total",
    "Extrativo_AT",
    "Extrativo_SGF",
    "TPC",
    "Idade",
    "vmi_le_021",
    "vmi_021_025",
    "vmi_gt_025",
    "pct_AB",
    "pct_C",
    "pct_DMG",
]
LAG_FEATURES = ["TSA_lag1", "TSA_roll3", "TSA_roll7"]
FAMILIES = [
    "randomforest",
    "extratrees",
    "histgradientboosting",
    "xgboost",
    "lightgbm",
    "catboost",
]
RANDOM_STATE = 42
HOLDOUT_FRACTION = 0.2
INTERVAL_Q = (0.10, 0.90)


def _load_ordered_frame() -> pd.DataFrame:
    cols = PROCESS_FEATURES + [TARGET]
    pointer_path = REPO / "data" / "l2_excel_validation" / "current.json.previous"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    train = pd.read_parquet(pointer["paths"]["train_features"])
    holdout = pd.read_parquet(pointer["paths"]["holdout_features"])
    l2 = pd.concat([train, holdout], ignore_index=True)
    frame = (
        l2.loc[l2[cols].notna().all(axis=1), cols + ["data_processo", "turno"]]
        .sort_values(["data_processo", "turno"])
        .reset_index(drop=True)
    )
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce")
    frame["TSA_lag1"] = frame[TARGET].shift(1)
    frame["TSA_roll3"] = frame[TARGET].shift(1).rolling(3, min_periods=3).mean()
    frame["TSA_roll7"] = frame[TARGET].shift(1).rolling(7, min_periods=7).mean()
    frame = frame.dropna(subset=LAG_FEATURES).reset_index(drop=True)
    return frame


def _engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame[PROCESS_FEATURES + LAG_FEATURES].copy()
    out["DB_c"] = frame["DB_LAB"] - 490.0
    out["DB_c2"] = out["DB_c"] ** 2
    out["TPC_crit"] = (frame["TPC"] < 45).astype(float)
    out["TPC_opt"] = ((frame["TPC"] >= 60) & (frame["TPC"] <= 90)).astype(float)
    out["Carga_crit"] = (frame["Carga_Alcalina"] > 21).astype(float)
    out["Carga_opt"] = (
        (frame["Carga_Alcalina"] >= 18.5) & (frame["Carga_Alcalina"] <= 20.5)
    ).astype(float)
    out["Extr_crit"] = (frame["Extrativo_AT"] > 2.45).astype(float)
    out["Extr_x_Carga"] = frame["Extrativo_AT"] * frame["Carga_Alcalina"]
    out["DB_x_Extr"] = out["DB_c"] * frame["Extrativo_AT"]
    out["TPC_x_VMIgt"] = frame["TPC"] * frame["vmi_gt_025"]
    return out


def _temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cut = int(len(df) * (1 - HOLDOUT_FRACTION))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _predict_level(pipe, X: pd.DataFrame, anchor: pd.Series) -> np.ndarray:
    return anchor.to_numpy() + pipe.predict(X)


def _cv_mae_residual(
    family: str,
    X: pd.DataFrame,
    y_residual: pd.Series,
    anchor: pd.Series,
    y_level: pd.Series,
    *,
    cv_folds: int,
) -> float:
    n_splits = min(cv_folds, max(2, len(X) // 80))
    tss = TimeSeriesSplit(n_splits=n_splits)
    maes: list[float] = []
    for train_idx, val_idx in tss.split(X):
        if family == "histgradientboosting":
            pipe = _base_pipeline(family, RANDOM_STATE, impute_optional=False)
        else:
            pipe = make_family(family, RANDOM_STATE)
        pipe.fit(X.iloc[train_idx], y_residual.iloc[train_idx])
        pred_level = _predict_level(pipe, X.iloc[val_idx], anchor.iloc[val_idx])
        maes.append(mean_absolute_error(y_level.iloc[val_idx], pred_level))
    return float(np.mean(maes))


def _oof_residuals(
    pipe,
    X: pd.DataFrame,
    y_residual: pd.Series,
    *,
    cv_folds: int,
) -> np.ndarray:
    n_splits = min(cv_folds, max(2, len(X) // 80))
    tss = TimeSeriesSplit(n_splits=n_splits)
    oof = np.full(len(X), np.nan)
    for train_idx, val_idx in tss.split(X):
        fold_pipe = clone(pipe)
        fold_pipe.fit(X.iloc[train_idx], y_residual.iloc[train_idx])
        oof[val_idx] = fold_pipe.predict(X.iloc[val_idx])
    return oof


def _plot_forecast(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_lo: np.ndarray,
    y_hi: np.ndarray,
    *,
    family: str,
    metrics: dict[str, float],
    baselines: dict[str, float],
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    ax.scatter(y_true, y_pred, alpha=0.45, s=20, color="#1d4ed8", edgecolors="none")
    lo = min(y_true.min(), y_pred.min(), y_lo.min())
    hi = max(y_true.max(), y_pred.max(), y_hi.max())
    ax.plot([lo, hi], [lo, hi], "--", color="#64748b", linewidth=1.2, label="y = x")
    ax.set_xlabel("TSA_dia real (t/dia)")
    ax.set_ylabel("TSA_dia predito (t/dia)")
    ax.set_title(
        f"Forecast operacional — {family}\n"
        f"MAE={metrics['mae']:.1f} | R²={metrics['r2']:.3f} "
        f"(lag1={baselines['lag1']:.1f}, roll3={baselines['roll3']:.1f})"
    )
    ax.legend(loc="upper left")
    ax.set_aspect("equal", adjustable="box")

    ax = axes[1]
    idx = np.arange(len(y_true))
    ax.fill_between(idx, y_lo, y_hi, alpha=0.25, color="#93c5fd", label="PI 80%")
    ax.plot(idx, y_true, color="#15803d", linewidth=1.2, label="Real")
    ax.plot(idx, y_pred, color="#dc2626", linewidth=1.0, linestyle="--", label="Predito")
    ax.set_xlabel("Índice temporal (holdout)")
    ax.set_ylabel("TSA_dia (t/dia)")
    ax.set_title("Série temporal — holdout")
    ax.legend(loc="best")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def main() -> None:
    raw = _load_ordered_frame()
    train_df, holdout_df = _temporal_split(raw)

    X_train = _engineer_features(train_df)
    X_holdout = _engineer_features(holdout_df)
    anchor_train = train_df[ANCHOR]
    anchor_holdout = holdout_df[ANCHOR]
    y_train = train_df[TARGET]
    y_holdout = holdout_df[TARGET]
    y_res_train = y_train - anchor_train

    tuning = TuningConfig(enabled=True, cv_folds=5, fast=False, n_jobs=-1)

    baselines = {
        "mean": mean_absolute_error(y_holdout, np.full(len(y_holdout), y_train.mean())),
        "lag1": mean_absolute_error(y_holdout, holdout_df["TSA_lag1"]),
        "roll3": mean_absolute_error(y_holdout, holdout_df["TSA_roll3"]),
        "roll7": mean_absolute_error(y_holdout, holdout_df["TSA_roll7"]),
    }

    print(f"Registros: total={len(raw)} train={len(train_df)} holdout={len(holdout_df)}")
    print(f"Âncora temporal: {ANCHOR}")
    print("\n== Baselines (holdout) ==")
    for name, mae in baselines.items():
        print(f"  {name:8s} MAE = {mae:7.2f}")

    print("\n== Famílias no resíduo (CV temporal → MAE nível) ==")
    cv_results: list[dict] = []
    for family in FAMILIES:
        try:
            cv_mae = _cv_mae_residual(
                family,
                X_train,
                y_res_train,
                anchor_train,
                y_train,
                cv_folds=tuning.cv_folds,
            )
            cv_results.append({"family": family, "cv_mae": cv_mae})
            print(f"  {family:22s} CV MAE = {cv_mae:7.2f}")
        except Exception as exc:
            print(f"  {family:22s} ERRO: {exc}")

    if not cv_results:
        raise RuntimeError("nenhuma família treinou com sucesso")

    cv_results.sort(key=lambda r: r["cv_mae"])
    champion = cv_results[0]["family"]
    print(f"\nCampeão: {champion} (CV MAE={cv_results[0]['cv_mae']:.2f})")

    print(f"\n== GridSearchCV — resíduo {champion} ==")
    best_pipe, grid_meta = fit_elo3_with_grid_search(
        X_train,
        y_res_train,
        champion,
        RANDOM_STATE,
        tuning,
        impute_optional=False,
    )
    print(f"  best_params: {grid_meta['best_params']}")
    print(f"  CV MAE resíduo (GridSearch): {grid_meta['cv_mae']:.2f}")

    y_pred = _predict_level(best_pipe, X_holdout, anchor_holdout)
    holdout_metrics = _metrics(y_holdout, y_pred)

    print("\n== Holdout temporal ==")
    print(f"  MAE  = {holdout_metrics['mae']:.2f}")
    print(f"  RMSE = {holdout_metrics['rmse']:.2f}")
    print(f"  R²   = {holdout_metrics['r2']:.3f}")

    oof_res = _oof_residuals(best_pipe, X_train, y_res_train, cv_folds=tuning.cv_folds)
    mask = ~np.isnan(oof_res)
    oof_level = anchor_train.to_numpy()[mask] + oof_res[mask]
    oof_true = y_train.to_numpy()[mask]
    resid = oof_true - oof_level
    q_lo, q_hi = np.quantile(resid, INTERVAL_Q)
    y_lo = y_pred + q_lo
    y_hi = y_pred + q_hi
    coverage = float(np.mean((y_holdout.to_numpy() >= y_lo) & (y_holdout.to_numpy() <= y_hi)))
    print(f"  PI 80% cobertura holdout: {coverage:.1%}")

    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    models_dir = REPO / "models" / "primeira_base" / f"forecast_{run_id}"
    models_dir.mkdir(parents=True, exist_ok=True)
    from simulation.forecast.predictor import ForecastArtifact, save_forecast_artifact

    artifact = ForecastArtifact(
        pipe=best_pipe,
        anchor=ANCHOR,
        feature_columns=list(X_train.columns),
        interval_quantiles={"q_lo": float(q_lo), "q_hi": float(q_hi)},
        family=champion,
        run_id=run_id,
    )
    artifact_path = models_dir / f"forecast_{champion}.joblib"
    save_forecast_artifact(artifact_path, artifact)

    pointer = {
        "run_id": run_id,
        "product": "forecast_operacional_A",
        "family": champion,
        "anchor": ANCHOR,
        "artifact_path": str(
            models_dir.relative_to(REPO) / f"forecast_{champion}.joblib"
        ),
        "holdout_metrics": holdout_metrics,
        "interval_80_coverage": coverage,
        "updated_at": run_id,
    }
    pointer_path = REPO / "models" / "primeira_base" / "current_forecast.json"
    pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, indent=2), encoding="utf-8")

    graphic_path = REPO / "graphics" / "tsa_forecast_operacional_real_vs_pred.png"
    _plot_forecast(
        y_holdout.to_numpy(),
        y_pred,
        y_lo,
        y_hi,
        family=champion,
        metrics=holdout_metrics,
        baselines=baselines,
        out_path=graphic_path,
    )

    report = {
        "run_id": run_id,
        "product": "forecast_operacional_A",
        "target": TARGET,
        "anchor": ANCHOR,
        "n_total": len(raw),
        "n_train": len(train_df),
        "n_holdout": len(holdout_df),
        "baselines_holdout_mae": baselines,
        "cv_ranking": cv_results,
        "champion": champion,
        "grid_search": grid_meta,
        "holdout_metrics": holdout_metrics,
        "interval_80_coverage": coverage,
        "interval_quantiles": {"q_lo": float(q_lo), "q_hi": float(q_hi)},
        "model_path": str(artifact_path),
        "graphic_path": str(graphic_path),
    }
    json_path = REPO / "reports" / "TSA_FORECAST_OPERACIONAL.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = REPO / "reports" / "TSA_FORECAST_OPERACIONAL.md"
    md_path.write_text(
        f"""# Forecast Operacional TSA (Produto A)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Base:** `base/primeira_base.csv` + lags temporais ({len(raw)} registros após lags)

## Estratégia

```
TSA_pred = TSA_roll3 + modelo_resíduo(features_processo + lags + FE)
```

## Baselines (holdout MAE)

| Baseline | MAE |
|----------|-----|
"""
        + "\n".join(f"| {k} | {v:.2f} |" for k, v in baselines.items())
        + f"""

## Campeão: `{champion}`

**GridSearch:** `{grid_meta['best_params']}`

| Métrica holdout | Valor |
|-----------------|-------|
| MAE | {holdout_metrics['mae']:.2f} |
| RMSE | {holdout_metrics['rmse']:.2f} |
| R² | {holdout_metrics['r2']:.3f} |
| Cobertura PI 80% | {coverage:.1%} |

## Gráfico

![Forecast operacional](../graphics/tsa_forecast_operacional_real_vs_pred.png)

## Modelo

`{report['model_path']}`
""",
        encoding="utf-8",
    )

    print(f"\nModelo: {artifact_path}")
    print(f"Gráfico: {graphic_path}")
    print(f"Relatório: {md_path}")


if __name__ == "__main__":
    main()

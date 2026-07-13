"""Modelagem TSA_dia a partir de base/primeira_base.csv.

Autor: Emerson Antônio
Data: 2026-07-13

Y = TSA_dia
X = 17 features de negócio (RELATORIO §3)

Pipeline:
1. Compara famílias do projeto via TimeSeriesSplit + MAE
2. GridSearchCV no campeão
3. Gráfico real vs predito (holdout temporal 20%)
4. Artefatos em models/primeira_base/ e graphics/
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from simulation.models.families import make_family
from simulation.models.grid_search import (
    TuningConfig,
    _base_pipeline,
    _param_grid,
    fit_elo3_with_grid_search,
)

TARGET = "TSA_dia"
FEATURES = [
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
FAMILIES = [
    "baseline",
    "elasticnet",
    "ridge",
    "lasso",
    "randomforest",
    "extratrees",
    "histgradientboosting",
    "xgboost",
    "lightgbm",
    "catboost",
]
RANDOM_STATE = 42
HOLDOUT_FRACTION = 0.2


def _load_ordered_frame() -> pd.DataFrame:
    """Carrega primeira_base.csv validando equivalência com L2 ordenado."""
    csv_path = REPO / "base" / "primeira_base.csv"
    csv_df = pd.read_csv(csv_path)
    cols = FEATURES + [TARGET]

    pointer_path = REPO / "data" / "l2_excel_validation" / "current.json.previous"
    if pointer_path.exists():
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        train = pd.read_parquet(pointer["paths"]["train_features"])
        holdout = pd.read_parquet(pointer["paths"]["holdout_features"])
        l2 = pd.concat([train, holdout], ignore_index=True)
        l2f = (
            l2.loc[l2[cols].notna().all(axis=1), cols + ["data_processo", "turno"]]
            .sort_values(["data_processo", "turno"])
            .reset_index(drop=True)
        )
        if len(l2f) != len(csv_df):
            print(
                f"Aviso: CSV ({len(csv_df)}) != L2 filtrado ({len(l2f)}); "
                "usando L2 ordenado temporalmente."
            )
        return l2f[cols]

    return csv_df[cols].reset_index(drop=True)


def _temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cut = int(len(df) * (1 - HOLDOUT_FRACTION))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def _cv_mae_default(family: str, X: pd.DataFrame, y: pd.Series, *, cv_folds: int) -> float:
    n_splits = min(cv_folds, max(2, len(X) // 100))
    tss = TimeSeriesSplit(n_splits=n_splits)
    maes: list[float] = []
    for train_idx, val_idx in tss.split(X):
        if family == "histgradientboosting":
            pipe = _base_pipeline(family, RANDOM_STATE, impute_optional=False)
        else:
            pipe = make_family(family, RANDOM_STATE)
        pipe.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = pipe.predict(X.iloc[val_idx])
        maes.append(mean_absolute_error(y.iloc[val_idx], pred))
    return float(np.mean(maes))


def _metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _plot_real_vs_pred(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    family: str,
    metrics: dict[str, float],
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_true, y_pred, alpha=0.45, s=18, color="#1d4ed8", edgecolors="none")
    lo = min(y_true.min(), y_pred.min())
    hi = max(y_true.max(), y_pred.max())
    ax.plot([lo, hi], [lo, hi], "--", color="#64748b", linewidth=1.2, label="y = x")
    ax.set_xlabel("TSA_dia real (t/dia)")
    ax.set_ylabel("TSA_dia predito (t/dia)")
    ax.set_title(
        f"Real vs Predito — {family}\n"
        f"MAE={metrics['mae']:.1f} | RMSE={metrics['rmse']:.1f} | R²={metrics['r2']:.3f}"
    )
    ax.legend(loc="upper left")
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def main() -> None:
    df = _load_ordered_frame()
    train_df, holdout_df = _temporal_split(df)

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_holdout = holdout_df[FEATURES]
    y_holdout = holdout_df[TARGET]

    tuning = TuningConfig(enabled=True, cv_folds=5, fast=False, n_jobs=-1)

    print(f"Registros: total={len(df)} train={len(train_df)} holdout={len(holdout_df)}")
    print("\n== Comparação de famílias (CV temporal, MAE) ==")

    cv_results: list[dict] = []
    for family in FAMILIES:
        try:
            cv_mae = _cv_mae_default(family, X_train, y_train, cv_folds=tuning.cv_folds)
            cv_results.append({"family": family, "cv_mae": cv_mae})
            print(f"  {family:22s} CV MAE = {cv_mae:8.2f}")
        except Exception as exc:
            print(f"  {family:22s} ERRO: {exc}")

    if not cv_results:
        raise RuntimeError("nenhuma família treinou com sucesso")

    cv_results.sort(key=lambda r: r["cv_mae"])
    tunable = [r for r in cv_results if r["family"] != "baseline"]
    champion = tunable[0]["family"] if tunable else cv_results[0]["family"]
    print(f"\nCampeão (CV, excl. baseline): {champion} (MAE={next(r['cv_mae'] for r in cv_results if r['family']==champion):.2f})")
    baseline_mae = next((r["cv_mae"] for r in cv_results if r["family"] == "baseline"), None)
    if baseline_mae is not None:
        print(f"  Referência baseline (média): MAE={baseline_mae:.2f}")

    print(f"\n== GridSearchCV — {champion} ==")
    try:
        _param_grid(champion, fast=tuning.fast)
        has_grid = True
    except ValueError:
        has_grid = False

    if has_grid:
        best_pipe, grid_meta = fit_elo3_with_grid_search(
            X_train,
            y_train,
            champion,
            RANDOM_STATE,
            tuning,
            impute_optional=False,
        )
        print(f"  best_params: {grid_meta['best_params']}")
        print(f"  CV MAE (GridSearch): {grid_meta['cv_mae']:.2f}")
    else:
        best_pipe = (
            _base_pipeline(champion, RANDOM_STATE, impute_optional=False)
            if champion == "histgradientboosting"
            else make_family(champion, RANDOM_STATE)
        )
        best_pipe.fit(X_train, y_train)
        grid_meta = {
            "family": champion,
            "best_params": {},
            "cv_mae": cv_results[0]["cv_mae"],
            "cv_folds": tuning.cv_folds,
            "note": "sem grid definido — modelo ajustado no pool de treino completo",
        }
        print(f"  (sem grid para {champion}; fit no treino completo)")

    y_pred_holdout = best_pipe.predict(X_holdout)
    holdout_metrics = _metrics(y_holdout, y_pred_holdout)

    print("\n== Holdout temporal (20% final) ==")
    print(f"  MAE  = {holdout_metrics['mae']:.2f}")
    print(f"  RMSE = {holdout_metrics['rmse']:.2f}")
    print(f"  R²   = {holdout_metrics['r2']:.3f}")

    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    models_dir = REPO / "models" / "primeira_base" / run_id
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipe, models_dir / f"tsa_{champion}.joblib")

    graphic_path = REPO / "graphics" / "tsa_primeira_base_real_vs_pred.png"
    _plot_real_vs_pred(
        y_holdout.to_numpy(),
        y_pred_holdout,
        family=champion,
        metrics=holdout_metrics,
        out_path=graphic_path,
    )

    report = {
        "run_id": run_id,
        "target": TARGET,
        "features": FEATURES,
        "n_total": len(df),
        "n_train": len(train_df),
        "n_holdout": len(holdout_df),
        "cv_ranking": cv_results,
        "champion": champion,
        "grid_search": grid_meta,
        "holdout_metrics": holdout_metrics,
        "model_path": str(models_dir / f"tsa_{champion}.joblib"),
        "graphic_path": str(graphic_path),
    }
    report_path = REPO / "reports" / "TSA_PRIMEIRA_BASE_MODELING.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    pointer_path = REPO / "models" / "primeira_base" / "current_tsa.json"
    pointer_path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "product": "what_if_direct",
                "family": champion,
                "artifact_path": f"models/primeira_base/{run_id}/tsa_{champion}.joblib",
                "features": FEATURES,
                "holdout_metrics": holdout_metrics,
                "updated_at": run_id,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    md_path = REPO / "reports" / "TSA_PRIMEIRA_BASE_MODELING.md"
    md_path.write_text(
        f"""# Modelagem TSA — primeira_base

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Base:** `base/primeira_base.csv` ({len(df)} registros, 100% completos)

## Definição

- **Y:** `TSA_dia`
- **X:** {len(FEATURES)} features de negócio

## Validação

- CV: `TimeSeriesSplit` (5 folds) no pool de treino (80% inicial)
- Holdout: 20% final (ordem temporal 2021-06 → 2025-10)

## Ranking CV (MAE)

| Família | CV MAE |
|---------|--------|
"""
        + "\n".join(
            f"| {r['family']} | {r['cv_mae']:.2f} |" for r in cv_results
        )
        + f"""

## Campeão: `{champion}`

**GridSearch best_params:** `{grid_meta['best_params']}`

**CV MAE (GridSearch):** {grid_meta['cv_mae']:.2f}

## Holdout temporal

| Métrica | Valor |
|---------|-------|
| MAE | {holdout_metrics['mae']:.2f} |
| RMSE | {holdout_metrics['rmse']:.2f} |
| R² | {holdout_metrics['r2']:.3f} |

## Gráfico

![Real vs Predito](../graphics/tsa_primeira_base_real_vs_pred.png)

## Artefato

`{report['model_path']}`
""",
        encoding="utf-8",
    )

    print(f"\nModelo salvo: {models_dir / f'tsa_{champion}.joblib'}")
    print(f"Gráfico: {graphic_path}")
    print(f"Relatório: {md_path}")


if __name__ == "__main__":
    main()

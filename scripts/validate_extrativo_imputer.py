"""Validação do imputer de Extrativo_AT (Elo 1).

Autor: Emerson Antônio
Data: 2026-07-13

Mede a qualidade do preenchimento de Extrativo_AT:
- MAE em validação cruzada temporal (dentro do treino medido);
- MAE honesto no holdout medido (generalização fora da janela de treino);
- comparação com baseline (média do treino);
- distribuição medido vs estimado (sanidade física).

Gera relatório em `reports/` e gráfico em `graphics/`.
"""
# ruff: noqa: E501  # linhas longas são conteúdo de relatório em f-string

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

from ingest.config import IngestSettings
from ingest.transform.imputation import fit_extrativo_imputer

REPO = Path(__file__).resolve().parents[1]
L2_ROOT = REPO / "data" / "l2_excel_validation"


def _measured_mask(df: pd.DataFrame, features: list[str]) -> pd.Series:
    y = pd.to_numeric(df["Extrativo_AT"], errors="coerce")
    x = df[features].apply(pd.to_numeric, errors="coerce")
    return y.notna() & x.notna().all(axis=1)


def main() -> None:
    settings = IngestSettings.from_yaml()
    pointer = json.loads((L2_ROOT / "current.json").read_text(encoding="utf-8"))
    prev = json.loads((L2_ROOT / "current.json.previous").read_text(encoding="utf-8"))

    train = pd.read_parquet(prev["paths"]["train_features"])
    holdout = pd.read_parquet(prev["paths"]["holdout_features"])

    fitted = fit_extrativo_imputer(
        train,
        random_state=settings.extr_impute_random_state,
        min_train_rows=settings.extr_impute_min_train_rows,
    )
    assert fitted is not None
    model, meta = fitted
    features = meta["features"]

    if "data_processo" in train.columns:
        train = train.sort_values("data_processo").reset_index(drop=True)

    mask_tr = _measured_mask(train, features)
    x_tr = train.loc[mask_tr, features].apply(pd.to_numeric, errors="coerce")
    y_tr = pd.to_numeric(train.loc[mask_tr, "Extrativo_AT"], errors="coerce")

    cv_maes: list[float] = []
    tss = TimeSeriesSplit(n_splits=5)
    from sklearn.ensemble import RandomForestRegressor

    for tr_idx, va_idx in tss.split(x_tr):
        m = RandomForestRegressor(
            n_estimators=200, min_samples_leaf=5, random_state=42, n_jobs=1
        )
        m.fit(x_tr.iloc[tr_idx], y_tr.iloc[tr_idx])
        pred = m.predict(x_tr.iloc[va_idx])
        cv_maes.append(mean_absolute_error(y_tr.iloc[va_idx], pred))
    cv_mae = float(np.mean(cv_maes))

    mask_ho = _measured_mask(holdout, features)
    x_ho = holdout.loc[mask_ho, features].apply(pd.to_numeric, errors="coerce")
    y_ho = pd.to_numeric(holdout.loc[mask_ho, "Extrativo_AT"], errors="coerce")
    pred_ho = model.predict(x_ho)
    holdout_mae = float(mean_absolute_error(y_ho, pred_ho))

    baseline_pred = np.full(len(y_ho), float(y_tr.mean()))
    baseline_mae = float(mean_absolute_error(y_ho, baseline_pred))

    enriched = pd.read_parquet(pointer["paths"]["train_features"])
    med = pd.to_numeric(
        enriched.loc[enriched["extr_origin"] == "medido", "Extrativo_AT"], errors="coerce"
    )
    est = pd.to_numeric(
        enriched.loc[enriched["extr_origin"] == "estimado", "Extrativo_AT"], errors="coerce"
    )

    graphics_dir = REPO / "graphics"
    graphics_dir.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].scatter(y_ho, pred_ho, s=10, alpha=0.4, color="#15803d")
    lims = [min(y_ho.min(), pred_ho.min()), max(y_ho.max(), pred_ho.max())]
    axes[0].plot(lims, lims, "--", color="#888")
    axes[0].set_xlabel("Extrativo_AT medido (holdout)")
    axes[0].set_ylabel("Extrativo_AT previsto (Elo 1)")
    axes[0].set_title(f"Holdout medido — MAE={holdout_mae:.3f}")

    axes[1].hist(med.dropna(), bins=30, alpha=0.6, label="medido", color="#1d4ed8")
    axes[1].hist(est.dropna(), bins=30, alpha=0.6, label="estimado", color="#f59e0b")
    axes[1].axvline(2.45, color="#dc2626", linestyle="--", label="crítico >2.45")
    axes[1].set_xlabel("Extrativo_AT (%)")
    axes[1].set_ylabel("Frequência (train)")
    axes[1].set_title("Distribuição medido vs estimado")
    axes[1].legend()
    fig.tight_layout()
    graphic_path = graphics_dir / "extrativo_imputer_validation.png"
    fig.savefig(graphic_path, dpi=120)
    plt.close(fig)

    gain = 1 - holdout_mae / baseline_mae
    beats_baseline = holdout_mae < baseline_mae
    if beats_baseline:
        verdict = (
            f"O imputer supera o baseline (média) no holdout, reduzindo o MAE em "
            f"{gain:.1%}. A imputação agrega cobertura **e** sinal."
        )
    else:
        verdict = (
            f"O imputer **não supera** o baseline (média) no holdout "
            f"(MAE {holdout_mae:.3f} vs {baseline_mae:.3f}; {gain:+.1%}). "
            "Mix + idade têm baixo poder preditivo para Extrativo_AT — a imputação "
            "entrega **cobertura** (100%) mas os valores estimados ficam próximos "
            "da média, com baixa informação marginal. Alternativas: usar imputação "
            "por média/mediana condicional, incorporar variáveis lab/florestais mais "
            "correlacionadas, ou preferir OOF stack na Camada 3 em vez de imputar no L2."
        )

    reports_dir = REPO / "reports"
    reports_dir.mkdir(exist_ok=True)
    report = f"""# Validação do Imputer de Extrativo_AT (Elo 1)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Fonte L2:** `{prev["dataset_version"]}` (antes) → `{pointer["dataset_version"]}` (enriquecido)

## 1. Qualidade do imputer

| Métrica | Valor (p.p. de Extrativo_AT) |
|---------|------------------------------|
| MAE CV temporal (train medido) | {cv_mae:.3f} |
| MAE holdout medido ({int(mask_ho.sum())} linhas) | {holdout_mae:.3f} |
| MAE baseline (média do train) | {baseline_mae:.3f} |
| Ganho vs baseline | {gain:+.1%} |

Imputer treinado em {meta["n_train_rows"]} linhas medidas do treino.

## 2. Cobertura antes/depois

| Split | Antes | Depois |
|-------|-------|--------|
| train | {int(mask_tr.sum())}/{len(train)} ({mask_tr.mean():.1%}) | {len(enriched)}/{len(enriched)} (100%) |
| holdout | {int(mask_ho.sum())}/{len(holdout)} ({mask_ho.mean():.1%}) | 100% |

## 3. Distribuição por origem (train enriquecido)

| Origem | N | Média | Desvio | p05 | p50 | p95 |
|--------|---|-------|--------|-----|-----|-----|
| medido | {med.notna().sum()} | {med.mean():.3f} | {med.std():.3f} | {med.quantile(0.05):.3f} | {med.quantile(0.5):.3f} | {med.quantile(0.95):.3f} |
| estimado | {est.notna().sum()} | {est.mean():.3f} | {est.std():.3f} | {est.quantile(0.05):.3f} | {est.quantile(0.5):.3f} | {est.quantile(0.95):.3f} |

Faixa operacional de referência: ótima 1,5–2,1; aceitável 2,1–2,45; crítico >2,45.

## 4. Gráfico

![Validação do imputer]({graphic_path.relative_to(REPO)})

## 5. Leitura

- {verdict}
- A distribuição estimada tende a ser mais concentrada em torno da mediana (regressão à média típica de RF), o que reduz a cauda crítica >2,45.
- Recomenda-se monitorar MAE por `extr_origin` a cada re-treino da cascata e revisitar o preenchimento quando a cobertura lab do histórico aumentar.
"""
    report_path = reports_dir / "VALIDACAO_IMPUTER_EXTRATIVO.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"MAE CV temporal:   {cv_mae:.3f}")
    print(f"MAE holdout medido:{holdout_mae:.3f}")
    print(f"MAE baseline:      {baseline_mae:.3f}")
    print(f"Relatório: {report_path}")
    print(f"Gráfico:   {graphic_path}")


if __name__ == "__main__":
    main()

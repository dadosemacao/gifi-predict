# Forecast Operacional TSA (Produto A)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Base:** `base/primeira_base.csv` + lags temporais (1895 registros após lags)

## Estratégia

```
TSA_pred = TSA_roll3 + modelo_resíduo(features_processo + lags + FE)
```

## Baselines (holdout MAE)

| Baseline | MAE |
|----------|-----|
| mean | 119.52 |
| lag1 | 57.77 |
| roll3 | 66.89 |
| roll7 | 75.32 |

## Campeão: `extratrees`

**GridSearch:** `{'model__max_depth': 12, 'model__max_features': 'sqrt', 'model__min_samples_leaf': 10, 'model__n_estimators': 200}`

| Métrica holdout | Valor |
|-----------------|-------|
| MAE | 67.61 |
| RMSE | 107.93 |
| R² | 0.252 |
| Cobertura PI 80% | 71.0% |

## Gráfico

![Forecast operacional](../graphics/tsa_forecast_operacional_real_vs_pred.png)

## Modelo

`/Users/emerson.antonio/Developar/keyrus/veracel/gifi-predict/models/primeira_base/forecast_2026-07-13T104544Z/forecast_extratrees.joblib`

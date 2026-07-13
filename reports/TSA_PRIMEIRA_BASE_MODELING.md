# Modelagem TSA — primeira_base

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Base:** `base/primeira_base.csv` (2012 registros, 100% completos)

## Definição

- **Y:** `TSA_dia`
- **X:** 13 features de negócio

## Validação

- CV: `TimeSeriesSplit` (5 folds) no pool de treino (80% inicial)
- Holdout: 20% final (ordem temporal 2021-06 → 2025-10)

## Ranking CV (MAE)

| Família | CV MAE |
|---------|--------|
| lasso | 87.04 |
| ridge | 87.11 |
| elasticnet | 87.30 |
| extratrees | 89.29 |
| randomforest | 92.25 |
| catboost | 92.67 |
| histgradientboosting | 99.96 |
| xgboost | 102.91 |
| baseline | 102.97 |
| lightgbm | 103.34 |

## Campeão: `lasso`

**GridSearch best_params:** `{'model__alpha': 1.0}`

**CV MAE (GridSearch):** 86.64

## Holdout temporal

| Métrica | Valor |
|---------|-------|
| MAE | 88.66 |
| RMSE | 120.12 |
| R² | 0.029 |

## Gráfico

![Real vs Predito](../graphics/tsa_primeira_base_real_vs_pred.png)

## Artefato

`/Users/emerson.antonio/Developar/keyrus/veracel/gifi-predict/models/primeira_base/2026-07-13T143520Z/tsa_lasso.joblib`

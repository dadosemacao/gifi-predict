# ML Tabular Quick Reference

> Fast lookup for GIFI cascade regression. **MCP Validated:** 2026-07-09

## Cascade map

| Elo | Target | Key inputs | MVP |
|-----|--------|------------|-----|
| 1 | Extrativo_AT | Sítio, Idade, mix | Yes |
| 1b | % Casca | — | NO-GO |
| 2 | Carga Alcalina | Extrativo, TPC, DB_SGF | Yes |
| 3 | TSA/dia | Mix A/B/C + qualidade + processo | Yes |

## Algorithms

| Family | Role |
|--------|------|
| Baseline | Mean / simple linear — mandatory |
| ElasticNet | Linear + L1/L2 — candidate |
| RandomForest | Non-linear — candidate |
| Neural net | Optional; champion only if A∧B∧C |

## Metrics & split

| Item | Contract |
|------|----------|
| MAE holdout | ≤ 56 TSA/dia (global) |
| Aux | RMSE, WAPE |
| Per elo | MAE_Extrativos, MAE_Carga, MAE_TSA |
| Train | ≤ 2025-04-30 |
| Holdout | 2025-05-01 .. 2025-10-30 |
| Split | Time-based (never random shuffle) |

## Physics (Matriz B)

| Stimulus ↑/↓ | TSA response |
|--------------|--------------|
| DB_LAB ↓ | TSA ↓ |
| Extrativo ↑ | TSA ↓ |
| TPC <45 ↓ | TSA ↓ |
| Carga ↑ | TSA ↓ |
| pct_ABC ↑ (dilutor) | TSA ↑ vs base |

## Matriz C / serving

| Item | Contract |
|------|----------|
| Top-3 | ΔTSA por cenário |
| RF | TreeExplainer (SHAP) |
| EN | `coef * x` documentado |
| Fallback | permutation_importance |
| API | FastAPI `/api/simulate` → curves + detractors |
| Prod bind | `demo=false` exige gate A∧B∧C |

## Decision matrix

| Use case | Choose |
|----------|--------|
| End-to-end scenario | Mode A |
| Diagnose one elo | Mode B inject |
| Release model | A∧B∧C + package |
| Tie on MAE | Prefer interpretability |

## Pitfalls

| Don't | Do |
|-------|-----|
| Shuffle train/test | Temporal cut D-A |
| Report only TSA MAE | Intermediate MAE too |
| Ship EN if B fails | Champion requires B∧C |
| Build Elo 1b in MVP | Feature Casca when measured |

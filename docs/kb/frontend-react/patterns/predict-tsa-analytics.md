# Pattern: Predict-TSA Analytics na UI

> **Purpose**: Renderizar curva de sensibilidade e top-3 local a partir do DTO de `/api/predict-tsa` — sem calcular Δ/sweep no cliente  
> **Autor**: Emerson Antônio · **Data**: 2026-07-13  
> **Fonte**: DESIGN_PREDICT_TSA_ANALYTICS

## Rules

1. Preferir `include_analytics=true` via query no `postPredictTsa`.
2. `SensitivityChart` e `LocalDetractorsList` são apresentacionais.
3. Não reutilizar `CurvesChart` / `DetractorsPanel` do `/simulate` (contratos distintos).
4. Labels PT-BR via `SENSITIVITY_VARIABLE_OPTIONS` em `types/predictTsa.ts`.

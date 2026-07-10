# Stage Metrics (MAE / RMSE / WAPE)

> **Purpose**: Contract metrics per elo and global TSA  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Fonte**: PRD §4.3 Matriz A

## Overview

Global gate: **MAE_TSA ≤ 56**.  
Per-elo MAE are mandatory report fields (not solo release gates).

## The Concept

```python
import numpy as np

def mae(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.mean(np.abs(y_true - y_pred)))

def rmse(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def wape(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    denom = np.sum(np.abs(y_true))
    return float(np.sum(np.abs(y_true - y_pred)) / denom) if denom else float("nan")
```

| Metric | Scope | Blocks release alone? |
|--------|-------|------------------------|
| MAE_TSA | Holdout global | Yes (≤56) + need B∧C |
| RMSE, WAPE | Report | No |
| MAE_Extrativos / MAE_Carga / MAE_TSA | Per elo | No (must report) |

## Quick Reference

| Report section | Required keys |
|----------------|---------------|
| Matriz A | mae, rmse, wape, n_holdout |
| Intermediate | mae_elo1, mae_elo2, mae_elo3 |
| Mode | A and B columns when applicable |

## Common Mistakes

### Wrong

“MAE next to 56” language; hiding intermediate blow-ups.

### Correct

Hard `<= 56` plus intermediate table in adherence report.

## Related

- [temporal-holdout.md](temporal-holdout.md)
- [../patterns/report-intermediate-mae.md](../patterns/report-intermediate-mae.md)

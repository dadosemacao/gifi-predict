# Temporal Holdout

> **Purpose**: Leakage-safe evaluation for industrial time series  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Sources**: DECISOES D-A; scikit-learn time-series split guidance

## Overview

Random shuffle overestimates performance on process data.  
GIFI uses a **calendar cut**, not k-fold CV for the release KPI.

## The Concept

| Partition | Dates | Use |
|-----------|-------|-----|
| Train | 2018-04 → **2025-04-30** | Fit + hyperparams |
| Holdout | **2025-05-01 → 2025-10-30** | Matriz A MAE≤56 |

```python
import pandas as pd

CUT = pd.Timestamp("2025-04-30")
HOLDOUT_END = pd.Timestamp("2025-10-30")

def temporal_split(df: pd.DataFrame, date_col: str = "data"):
    d = pd.to_datetime(df[date_col])
    train = df.loc[d <= CUT]
    holdout = df.loc[(d > CUT) & (d <= HOLDOUT_END)]
    return train, holdout
```

sklearn notes: shuffled `train_test_split` is optimistic for time-ordered data — use time-based split / TimeSeriesSplit for diagnostics only.

## Quick Reference

| Rule | Value |
|------|-------|
| MAE contract window | Holdout only |
| Features from future | Forbidden |
| Elo1 Lab coverage | Prefer periods with Extrativo coverage |

## Common Mistakes

### Wrong

Including May–Oct 2025 rows in training “for more data”.

### Correct

Hard cut at 2025-04-30 for any feature/label used at fit time.

## Related

- [stage-metrics.md](stage-metrics.md)
- [cascade-regression.md](cascade-regression.md)

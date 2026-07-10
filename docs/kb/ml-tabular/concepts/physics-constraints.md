# Physics Constraints / Monotonicity

> **Purpose**: Matriz B — directional stress tests for industrial plausibility  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Fonte**: PRD §4.3 Matriz B; CASOS_TESTE_FUNCIONAIS

## Overview

Statistical fit alone is insufficient. Holding other inputs fixed, the model must respond in the required direction under stress scenarios (TC/TM).

## The Concept

| Stimulus | Expected TSA | Rationale |
|----------|--------------|-----------|
| DB_LAB ↓ | ↓ or flat | Lower density → less pulp |
| VMI ↓ | ↓ | Lower wood volume index |
| Extrativo_AT ↑ | ↓ | Extractives hurt yield |
| TPC < 45 and ↓ | ↓ | Green wood penalty |
| Carga Alcalina ↑ | ↓ | Over-alkali regime |
| ↑ pct_ABC vs dry C base | ↑ | Dilutor mix lift |

```python
def check_monotonic(base_pred: float, stressed_pred: float, expect: str) -> bool:
    """expect in {'down', 'up', 'non_up'}."""
    if expect == "down":
        return stressed_pred < base_pred
    if expect == "non_up":
        return stressed_pred <= base_pred
    if expect == "up":
        return stressed_pred > base_pred
    raise ValueError(expect)
```

## Quick Reference

| Gate | Role |
|------|------|
| Matriz A | Accuracy |
| Matriz B | Physics (this file) |
| Matriz C | Top-3 ΔTSA |

Failing any Matriz B TC → candidate cannot be champion.

## Common Mistakes

### Wrong

Tweaking only global MAE and skipping stress suite.

### Correct

Automate TC/TM vectors; archive pass/fail with candidate id.

## Related

- [stage-metrics.md](stage-metrics.md)
- [../patterns/train-select-champion.md](../patterns/train-select-champion.md)

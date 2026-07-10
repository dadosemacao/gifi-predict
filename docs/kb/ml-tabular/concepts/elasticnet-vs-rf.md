# ElasticNet vs RandomForest

> **Purpose**: Candidate model families for GIFI MVP champion selection  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Sources**: PRD §4.2; scikit-learn ElasticNet / RandomForestRegressor

## Overview

Mandatory: Baseline + ElasticNet + RandomForest.  
NN optional (Marco 3); becomes champion only if it wins A∧B∧C.

## The Concept

| Family | Strength | Weakness | Tie-break |
|--------|----------|----------|-----------|
| Baseline | Audit floor | Low capacity | Most interpretable |
| ElasticNet | Sparse linear, stable | Misses interactions | Preferred if MAE close |
| RandomForest | Non-linear interactions | Less transparent | Needs Matriz C rigor |

```python
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor

en = ElasticNet(alpha=0.08, l1_ratio=0.5, random_state=0)
rf = RandomForestRegressor(
    n_estimators=200, max_depth=None, min_samples_leaf=5, random_state=0, n_jobs=-1
)
```

Policy: best holdout MAE **if** physical + explainability gates pass; on ties, interpretability > complexity.

## Quick Reference

| Requirement | EN | RF | Baseline |
|-------------|----|----|----------|
| MVP candidate | Yes | Yes | Yes |
| Feature scale | Yes (StandardScaler) | Optional | Yes |
| Feature importance | Coefs | Impurity / SHAP | N/A |

## Common Mistakes

### Wrong

Picking RF solely on train MAE without Matriz B.

### Correct

Score all on temporal holdout; run physics TCs; then select.

## Related

- [cascade-regression.md](cascade-regression.md)
- [../patterns/train-select-champion.md](../patterns/train-select-champion.md)

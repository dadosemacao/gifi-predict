# Train Candidates + Select Champion

> **Purpose**: Reproducible fit → score → gate → pick winner  
> **MCP Validated**: 2026-07-09

## When to Use

- Marco 1–3 training loops
- Replacing a rejected champion
- Optional NN bake-off

## Implementation

```python
from dataclasses import dataclass
from pathlib import Path
import joblib

@dataclass
class Candidate:
    name: str
    pipeline: object
    mae: float
    b_ok: bool
    c_ok: bool
    interpretability: int

def select_champion(cands: list[Candidate], mae_max: float = 56.0) -> Candidate | None:
    ok = [c for c in cands if c.mae <= mae_max and c.b_ok and c.c_ok]
    if not ok:
        return None
    return sorted(ok, key=lambda c: (c.mae, c.interpretability))[0]

def fit_and_score(pipelines: dict, X_tr, y_tr, X_ho, y_ho, phys_fn, expl_fn):
    out = []
    for name, pipe in pipelines.items():
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_ho)
        mae = float(abs(pred - y_ho).mean())
        out.append(Candidate(
            name=name, pipeline=pipe, mae=mae,
            b_ok=phys_fn(pipe), c_ok=expl_fn(pipe, X_ho),
            interpretability={"baseline": 1, "elasticnet": 2, "rf": 3}.get(name, 9),
        ))
    return out

def persist_champion(c: Candidate, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"name": c.name, "mae": c.mae, "model": c.pipeline}, path)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `mae_max` | 56 | Matriz A |
| families | baseline, en, rf | MVP |
| seed | fixed | Reproducibility |

## Example Usage

Train three pipes on temporal train; score holdout; run phys/expl gates; dump champion only if selected.

## See Also

- [artifact-packaging.md](artifact-packaging.md)
- [../concepts/elasticnet-vs-rf.md](../concepts/elasticnet-vs-rf.md)

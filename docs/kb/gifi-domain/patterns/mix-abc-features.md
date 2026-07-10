# Mix A/B/C Features

> **Purpose**: Features auditáveis de abastecimento por camada A/B/C  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §3.3

## When to Use

- Feature engineering no Ingest (I3) e datasets de treino
- Validação unitária de features (D-10)
- Relatório de aceitação de representação (TC-A02)

## Implementation

```python
from __future__ import annotations
import numpy as np

SITES = ("A", "B", "C", "D", "MG")

def layer_a(pct: dict[str, float]) -> dict[str, float]:
    """Camada A — percentuais absolutos (soma ≈ 1)."""
    return {f"pct_{s}": float(pct[s]) for s in SITES}

def layer_b(pct: dict[str, float]) -> dict[str, float]:
    """Camada B — compostos crescimento rápido vs densas/secas."""
    return {
        "pct_ABC": pct["A"] + pct["B"] + pct["C"],
        "pct_CDMG": pct["C"] + pct["D"] + pct["MG"],
    }

def layer_c(pct: dict[str, float], dom_thresh: float = 0.50) -> dict[str, float]:
    """Camada C — diversidade e dominância."""
    vals = np.array([pct[s] for s in SITES], dtype=float)
    vals = np.clip(vals, 0.0, None)
    s = vals.sum()
    p = vals / s if s > 0 else vals
    ent = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    hhi = float((p ** 2).sum())
    out = {"mix_entropy": ent, "mix_hhi": hhi}
    for i, site in enumerate(SITES):
        out[f"dom_{site}"] = 1.0 if pct[site] > dom_thresh else 0.0
    return out

def assert_mix_sum(pct: dict[str, float], tol: float = 0.02) -> None:
    total = sum(pct[s] for s in SITES)
    if abs(total - 1.0) > tol:
        raise ValueError(f"mix sum={total} outside 1±{tol}")
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `mix_tol` | ±0,02 | Tolerância da soma |
| `dom_thresh` | 0,50 | Flag `dom_X` |
| `sites` | A,B,C,D,MG | Cobertura obrigatória |

## Example Usage

Gerar colunas A+B+C no mesmo frame turno antes de Elo 3; validar soma e unit tests das fórmulas.

## See Also

- [../concepts/mix-feature-layers.md](../concepts/mix-feature-layers.md)
- [turno-dia-aggregation.md](turno-dia-aggregation.md)

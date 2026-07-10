# Turno → Dia Aggregation

> **Purpose**: Agregar turno industrial para meta diária sem leakage  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: DECISOES D-C; PRD §3.1 / §3.4

## When to Use

- Consolidar dataset turno → dia para negócio / UI
- Qualidade ponderada por volume (DB, Extrativos, Casca)
- Particionar treino/holdout por calendário civil

## Implementation

```python
from __future__ import annotations
import pandas as pd

QUALITY_COLS = ["DB_LAB", "Extrativo_AT", "Casca_pct"]  # Casca se medida
SUM_COLS = ["Volume_m3"]
TSA_COL = "Producao_Digestor"  # meta diária = consolidação do dia

def volume_weighted_mean(g: pd.DataFrame, col: str, vol: str = "Volume_m3") -> float:
    w = g[vol].astype(float)
    x = g[col].astype(float)
    mask = w.notna() & x.notna() & (w > 0)
    if not mask.any():
        return float("nan")
    return float((x[mask] * w[mask]).sum() / w[mask].sum())

def aggregate_turno_to_dia(df: pd.DataFrame, date_col: str = "data") -> pd.DataFrame:
    """D-C: qualidade ponderada; volume soma; TSA = meta diária."""
    rows = []
    for day, g in df.groupby(date_col, sort=True):
        row = {date_col: day}
        for c in QUALITY_COLS:
            if c in g.columns:
                row[c] = volume_weighted_mean(g, c)
        for c in SUM_COLS:
            if c in g.columns:
                row[c] = float(g[c].sum())
        if TSA_COL in g.columns:
            # Meta diária: soma de produção do dia (negócio)
            row["TSA_dia"] = float(g[TSA_COL].sum())
        rows.append(row)
    return pd.DataFrame(rows)
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| qualidade | média ponderada por volume | D-C |
| volume | soma | D-C |
| TSA | meta diária | alvo de negócio |
| holdout | por data civil | D-A |

## Example Usage

Treino permanece em granularidade turno se o motor exigir; UI e KPIs de negócio consomem agregação diária.

## See Also

- [volume-weighted-quality.md](volume-weighted-quality.md)
- [../concepts/closed-decisions.md](../concepts/closed-decisions.md)

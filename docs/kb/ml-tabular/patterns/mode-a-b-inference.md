# Mode A Integration vs Mode B Isolation Inference

> **Purpose**: Run cascade end-to-end or with injected intermediates  
> **MCP Validated**: 2026-07-09

## When to Use

- Long-horizon scenario simulation (Mode A)
- Stress / diagnostic TC suite (Mode B)
- Comparing compounding vs stage skill

## Implementation

```python
from dataclasses import dataclass

@dataclass
class ScenarioRow:
    features: dict
    mode: str  # "A" | "B"
    extrativo_at: float | None = None
    carga: float | None = None
    db_lab: float | None = None

def infer_cascade(row: ScenarioRow, elo1, elo2, elo3) -> dict:
    x = dict(row.features)
    if row.mode == "B" and row.extrativo_at is not None:
        extr = row.extrativo_at
    else:
        extr = float(elo1.predict([x])[0])
    x["Extrativo_AT"] = extr

    if row.mode == "B" and row.carga is not None:
        carga = row.carga
    else:
        carga = float(elo2.predict([x])[0])
    x["Carga_Alcalina"] = carga

    if row.db_lab is not None:
        x["DB_LAB"] = row.db_lab
    elif "DB_LAB" not in x and "DB_SGF" in x:
        x["DB_LAB"] = 0.985 * float(x["DB_SGF"])

    tsa = float(elo3.predict([x])[0])
    return {"Extrativo_AT": extr, "Carga_Alcalina": carga, "TSA_dia": tsa, "mode": row.mode}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Mode A inject | forbidden | Domain template |
| Mode B inject | Extrativo, Carga, DB_LAB | Allowed |
| DB missing | 0.985×DB_SGF | Domain rule |

## Example Usage

Homologation: Mode A paths for UI demos; Mode B for Matriz B TC vectors.

## See Also

- [../concepts/cascade-regression.md](../concepts/cascade-regression.md)
- gifi-domain `mode-a-b` + `scenario-column-contract`

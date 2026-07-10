# Report Intermediate MAE

> **Purpose**: Make cascade error propagation visible  
> **MCP Validated**: 2026-07-09

## When to Use

- Homologation / adherence report
- Debugging Mode A vs Mode B gaps
- Champion decision packets

## Implementation

```python
from dataclasses import asdict, dataclass
import json
from pathlib import Path

@dataclass
class IntermediateMaeReport:
    mode: str  # A | B
    mae_extrativos: float
    mae_carga: float
    mae_tsa: float
    rmse_tsa: float
    wape_tsa: float
    n: int
    holdout_start: str = "2025-05-01"
    holdout_end: str = "2025-10-30"

def write_report(report: IntermediateMaeReport, path: Path) -> None:
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

def compare_modes(rep_a: IntermediateMaeReport, rep_b: IntermediateMaeReport) -> dict:
    """Compounding gap = Mode A TSA MAE − Mode B TSA MAE (diagnostic)."""
    return {
        "delta_mae_tsa_A_minus_B": rep_a.mae_tsa - rep_b.mae_tsa,
        "elo1": {"A": rep_a.mae_extrativos, "B": rep_b.mae_extrativos},
        "elo2": {"A": rep_a.mae_carga, "B": rep_b.mae_carga},
    }
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| modes | A and B | Always dual when possible |
| precision | 2 decimals | TSA units |
| blockers | only global MAE | Intermediates are mandatory fields |

## Example Usage

Attach JSON to release package; UI may surface summary, but Camada 4 owns the gate.

## See Also

- [../concepts/stage-metrics.md](../concepts/stage-metrics.md)
- [mode-a-b-inference.md](mode-a-b-inference.md)

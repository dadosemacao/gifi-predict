# Artifact Packaging for Release Gate

> **Purpose**: Package models + metrics so Camada 4 can gate Camada 5  
> **MCP Validated**: 2026-07-09

## When to Use

- After champion selection
- Before UI can bind a production inference API
- Audit / reproducibility packs

## Implementation

```python
from pathlib import Path
import json
import hashlib
import joblib
from datetime import datetime, timezone

def package_release(
    model_path: Path,
    metrics: dict,
    matriz_flags: dict,
    out_dir: Path,
    model_id: str,
) -> Path:
    """Release only if A∧B∧C; write manifest beside joblib."""
    assert matriz_flags.get("A") and matriz_flags.get("B") and matriz_flags.get("C")
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = model_path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    dest = out_dir / f"{model_id}.joblib"
    dest.write_bytes(blob)
    manifest = {
        "model_id": model_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
        "metrics": metrics,
        "matriz": matriz_flags,
        "holdout": {"start": "2025-05-01", "end": "2025-10-30"},
        "elo1b": "NO-GO",
        "gate": "A_and_B_and_C",
    }
    man = out_dir / f"{model_id}.manifest.json"
    man.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return man
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| format | joblib + JSON | Assumed CD |
| datasets | Parquet refs | Link ingest versions |
| demo vs prod | flag | UI demo may use non-gated builds |

## Example Usage

CI step: fail if any matriz false; publish `models/champion/` only on green gate.

## See Also

- [train-select-champion.md](train-select-champion.md)
- [report-intermediate-mae.md](report-intermediate-mae.md)

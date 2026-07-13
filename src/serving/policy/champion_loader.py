from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sklearn.pipeline import Pipeline

from simulation.package.publisher import load_pipeline


def load_production_champion_pipes(
    models_root: Path,
) -> tuple[dict[str, Pipeline], dict[str, list[str]], dict[str, Any]]:
    pointer_path = models_root / "current_champion.json"
    if not pointer_path.exists():
        raise FileNotFoundError(f"current_champion.json not found under {models_root}")

    ptr = json.loads(pointer_path.read_text(encoding="utf-8"))
    champion_dir = Path(ptr["champion_dir"])
    if not champion_dir.is_dir():
        raise FileNotFoundError(f"champion dir not found: {champion_dir}")

    manifest_path = champion_dir / "champion_manifest.json"
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    candidate_dir = Path(
        manifest.get("l3_candidate_dir", champion_dir)
    )
    feature_cols: dict[str, list[str]] = {}
    candidate_manifest = candidate_dir / "candidate_manifest.json"
    if candidate_manifest.exists():
        cm = json.loads(candidate_manifest.read_text(encoding="utf-8"))
        feature_cols = cm.get("feature_cols", {})

    champions = ptr.get("champions", {})
    pipes: dict[str, Pipeline] = {}
    for elo, family in champions.items():
        rel = ptr.get("artifacts", {}).get(elo)
        if rel:
            path = Path(rel)
            if not path.is_absolute():
                path = champion_dir / path.name
        else:
            path = champion_dir / f"{elo}_{family}.joblib"
        pipes[elo] = load_pipeline(path, models_root)

    pointer = {
        "run_id": ptr.get("run_id"),
        "champion_dir": str(champion_dir),
        "champions": champions,
        "artifacts": ptr.get("artifacts", {}),
    }
    return pipes, feature_cols, pointer

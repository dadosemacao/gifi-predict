from __future__ import annotations

import json
from typing import Any

from simulation.cascade.evaluator import evaluate_holdout
from simulation.config import SimulationSettings
from simulation.features.elo_specs import default_elo_specs
from simulation.l2.loader import load_l2_bundle
from simulation.package.publisher import load_champion_pipes, load_pipeline


def run_evaluate_pipeline(
    settings: SimulationSettings,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    bundle = load_l2_bundle(settings.l2_path, max_retries=settings.max_retries)
    specs = settings.elo_specs or default_elo_specs()

    if run_id:
        candidate_dir = settings.models_path / "candidates" / run_id
        manifest = json.loads(
            (candidate_dir / "candidate_manifest.json").read_text(encoding="utf-8")
        )
        champions = manifest["champions"]
        feature_cols = manifest["feature_cols"]
        pipes = {
            elo: load_pipeline(
                candidate_dir / f"{elo}_{family}.joblib",
                settings.models_path,
            )
            for elo, family in champions.items()
        }
    else:
        pipes, feature_cols, pointer = load_champion_pipes(settings.models_path)
        champions = pointer["champions"]
        run_id = pointer["run_id"]

    fitted = {elo: {champions[elo]: pipes[elo]} for elo in champions}
    metrics = evaluate_holdout(
        fitted,
        champions,
        bundle.holdout,
        specs,
        feature_cols,
        db_proxy_factor=settings.db_proxy_factor,
    )
    return {"run_id": run_id, "metrics": metrics}

from __future__ import annotations

from typing import Any

from simulation.cascade.evaluator import evaluate_holdout
from simulation.config import SimulationSettings
from simulation.features.elo_specs import default_elo_specs
from simulation.l2.loader import load_l2_bundle
from simulation.package.publisher import (
    load_candidate_pipes_by_run_id,
    load_champion_pipes,
)


def run_evaluate_pipeline(
    settings: SimulationSettings,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    bundle = load_l2_bundle(settings.l2_path, max_retries=settings.max_retries)
    specs = settings.elo_specs or default_elo_specs()

    if run_id:
        pipes, feature_cols, pointer = load_candidate_pipes_by_run_id(
            settings.models_path, run_id
        )
        champions = pointer["champions"]
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

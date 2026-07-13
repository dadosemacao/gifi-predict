from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from simulation.cascade.evaluator import evaluate_holdout
from simulation.config import SimulationSettings
from simulation.features.elo_specs import default_elo_specs
from simulation.l2.guard import (
    guard_holdout_eligible,
    guard_schema,
    validate_holdout_window,
)
from simulation.l2.loader import load_l2_bundle
from simulation.models.cascade_training import enrich_elo3_cascade_features, pick_elo12_fill_pipes
from simulation.models.selector import select_champions
from simulation.models.trainer import train_all
from simulation.observability.logging import log_simulate_end, log_simulate_start
from simulation.package.atomic_io import atomic_write_json
from simulation.package.manifest import build_candidate_manifest, extract_explainability
from simulation.package.publisher import publish_candidate


def run_train_pipeline(settings: SimulationSettings) -> dict[str, Any]:
    run_id = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_file = settings.logs_path / f"simulate_{run_id.replace(':', '-')}.jsonl"
    started = time.perf_counter()

    bundle = load_l2_bundle(settings.l2_path, max_retries=settings.max_retries)
    specs = settings.elo_specs or default_elo_specs()

    guard_schema(bundle.manifest, settings.expected_schema_version)
    guard_holdout_eligible(bundle.manifest)
    validate_holdout_window(
        bundle.holdout,
        start=settings.holdout_start,
        end=settings.holdout_end,
    )

    log_simulate_start(
        run_id=run_id,
        component="train",
        l2_dataset_version=bundle.dataset_version,
        l2_source_hash=bundle.source_hash,
        log_file=log_file,
    )

    tuning = settings.tuning_config()
    fitted, exclusions, feature_cols, tuning_meta = train_all(
        bundle.train,
        specs,
        settings.families,
        settings.random_state,
        min_train_rows=settings.min_train_rows,
        holdout=bundle.holdout,
        tuning=tuning,
        training_mode=settings.training_mode,
    )
    holdout_eval = bundle.holdout
    if tuning.enabled and tuning.elo3_cascade_fill:
        fitted_elo12 = pick_elo12_fill_pipes(fitted, settings.families)
        holdout_eval = enrich_elo3_cascade_features(
            bundle.holdout, fitted_elo12, specs
        )
    champions = select_champions(
        fitted,
        holdout_eval,
        specs,
        families=settings.families,
        feature_cols=feature_cols,
        db_proxy_factor=settings.db_proxy_factor,
        select_by_cascade=tuning.enabled and tuning.select_by_cascade,
        elo3_families=tuning.elo3_families if tuning.enabled else None,
        training_mode=settings.training_mode,
    )
    metrics = evaluate_holdout(
        fitted,
        champions,
        bundle.holdout,
        specs,
        feature_cols,
        db_proxy_factor=settings.db_proxy_factor,
        holdout_elo3=holdout_eval if tuning.enabled and tuning.elo3_cascade_fill else None,
        training_mode=settings.training_mode,
    )
    metrics["tuning"] = tuning_meta

    champion_pipes = {elo: fitted[elo][champions[elo]] for elo in champions}
    explainability = extract_explainability(fitted, champions, feature_cols)
    mae_value = metrics.get(
        "mae_primary",
        metrics["mae_tsa_cascade"]
        if settings.mae_metric == "cascade"
        else metrics["mae_tsa_isolated"],
    )
    release_ok = mae_value <= settings.mae_limit_report

    manifest_base = {
        "run_id": run_id,
        "l2": {
            "dataset_version": bundle.dataset_version,
            "schema_version": bundle.schema_version,
            "source_hash": bundle.source_hash,
            "paths": {k: str(v) for k, v in bundle.paths.items()},
        },
        "champions": champions,
        "feature_cols": feature_cols,
        "random_state": settings.random_state,
        "exclusions": exclusions,
        "tuning": tuning_meta,
        "artifacts": {},
    }

    candidate_dir = publish_candidate(
        settings.models_path,
        run_id,
        champion_pipes,
        champions,
        manifest_base,
        metrics,
        explainability,
        release_ok=release_ok,
        lock_timeout_s=float(settings.lock_timeout_s),
        max_retries=settings.max_retries,
    )

    artifact_paths = {
        elo: candidate_dir / f"{elo}_{champions[elo]}.joblib" for elo in champions
    }
    final_manifest = build_candidate_manifest(
        run_id=run_id,
        l2_dataset_version=bundle.dataset_version,
        l2_schema_version=bundle.schema_version,
        l2_source_hash=bundle.source_hash,
        l2_paths={k: str(v) for k, v in bundle.paths.items()},
        champions=champions,
        random_state=settings.random_state,
        exclusions=exclusions,
        feature_cols=feature_cols,
        artifact_paths=artifact_paths,
    )
    final_manifest["release_ok"] = release_ok
    atomic_write_json(candidate_dir / "candidate_manifest.json", final_manifest)

    duration_ms = int((time.perf_counter() - started) * 1000)
    log_simulate_end(
        run_id=run_id,
        component="train",
        duration_ms=duration_ms,
        mae_tsa_cascade=metrics["mae_tsa_cascade"],
        families_selected=champions,
        release_ok=release_ok,
        log_file=log_file,
    )

    return {
        "run_id": run_id,
        "candidate_dir": str(candidate_dir),
        "champions": champions,
        "metrics": metrics,
        "release_ok": release_ok,
    }

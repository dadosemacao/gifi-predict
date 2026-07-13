from __future__ import annotations

from pathlib import Path

import pandas as pd

from acceptance.matrices.matriz_c import top3_detractors
from ingest.config import IngestSettings
from ingest.online.infer_publish import publish_infer_features
from serving.errors import candidate_not_found, publish_error_to_http
from serving.policy.champion_loader import load_production_champion_pipes
from serving.policy.release import ReleaseContext
from serving.schemas import DetractorOut, InferenceResponse
from serving.services.curves import build_curves
from serving.services.detractors import build_elo3_explain_row
from simulation.cascade.inference import infer_dataframe
from simulation.config import SimulationSettings
from simulation.package.publisher import load_candidate_pipes_by_run_id


def run_simulate_upload(
    path: Path,
    *,
    cenario_id: str,
    mode: str,
    release_ctx: ReleaseContext,
    demo: bool,
    ingest_settings: IngestSettings | None = None,
    sim_settings: SimulationSettings | None = None,
) -> InferenceResponse:
    ingest = ingest_settings or IngestSettings.from_yaml()
    sim = sim_settings or SimulationSettings.from_yaml(ingest.repo_root)

    try:
        publish_infer_features(path, cenario_id, ingest)
    except ValueError as exc:
        raise publish_error_to_http(exc) from exc

    use_demo = demo or not release_ctx.release_ok
    try:
        if use_demo:
            pipes, feature_cols, pointer = load_candidate_pipes_by_run_id(
                sim.models_path, release_ctx.run_id
            )
        else:
            pipes, feature_cols, pointer = load_production_champion_pipes(
                sim.models_path
            )
    except FileNotFoundError as exc:
        raise candidate_not_found(release_ctx.run_id) from exc

    infer_path = ingest.l2_path / "scenarios" / cenario_id / "infer_features.parquet"
    df = pd.read_parquet(infer_path)
    preds = infer_dataframe(
        df,
        mode,
        pipes,
        feature_cols,
        db_proxy_factor=sim.db_proxy_factor,
    )

    merged = df.copy()
    for col in ("TSA_dia", "Carga_Alcalina", "Extrativo_AT"):
        if col in preds.columns:
            merged[col] = preds[col].values
    if "Volume" in merged.columns and "Volume_m3" not in merged.columns:
        merged["Volume_m3"] = merged["Volume"]

    sort_col = "linha" if "linha" in merged.columns else merged.columns[0]
    anchor_idx = merged.sort_values(sort_col).index[0]
    x_row = build_elo3_explain_row(merged.loc[[anchor_idx]], feature_cols["elo3"])
    family = pointer.get("champions", {}).get("elo3", "unknown")
    detractors = top3_detractors(
        pipes["elo3"], family, x_row, feature_cols["elo3"]
    )

    return InferenceResponse(
        mode=mode.upper(),  # type: ignore[arg-type]
        demo=use_demo,
        gate_ok=release_ctx.release_ok,
        model_id=release_ctx.run_id,
        acceptance_run_id=release_ctx.run_id,
        l2_dataset_version=release_ctx.l2_dataset_version,
        curves=build_curves(merged),
        detractors=[DetractorOut(**d) for d in detractors],
        warnings=[],
        metrics={"mae_tsa_holdout": release_ctx.mae_tsa_holdout},
    )

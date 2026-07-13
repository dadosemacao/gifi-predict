from __future__ import annotations

from pathlib import Path

import pandas as pd

from serving.policy.ingest_config import load_db_proxy_factor
from serving.policy.tsa_loader import load_tsa_direct_context
from serving.schemas import HoldoutMetricsResponse, PredictTsaResponse
from serving.services.field_origins import build_field_origins
from serving.services.resolve_process_fields import resolve_process_fields


def run_predict_tsa(
    body: dict,
    *,
    repo_root: Path,
    models_root: Path | None = None,
    run_id: str | None = None,
) -> PredictTsaResponse:
    resolved = resolve_process_fields(
        body,
        repo_root=repo_root,
        db_proxy_factor=load_db_proxy_factor(repo_root),
    )
    pipe, ctx = load_tsa_direct_context(
        repo_root, models_root=models_root, run_id=run_id
    )
    col_map = {
        "carga_alcalina": "Carga_Alcalina",
        "kappa": "Kappa",
        "db_sgf": "DB_SGF",
        "db_lab": "DB_LAB",
        "secura_pct": "Secura_pct",
        "casca_pct": "Casca_pct",
        "extrativo_total": "Extrativo_Total",
        "extrativo_at": "Extrativo_AT",
        "extrativo_sgf": "Extrativo_SGF",
        "tpc": "TPC",
        "idade": "Idade",
        "vmi_le_021": "vmi_le_021",
        "vmi_021_025": "vmi_021_025",
        "vmi_gt_025": "vmi_gt_025",
        "pct_ab": "pct_AB",
        "pct_c": "pct_C",
        "pct_dmg": "pct_DMG",
    }
    model_frame = pd.DataFrame(
        [{col_map[k]: resolved.values[k] for k in col_map if k in resolved.values}]
    )
    missing = [c for c in ctx.features if c not in model_frame.columns]
    if missing:
        raise ValueError(f"features ausentes após resolução: {missing}")
    tsa_dia = float(pipe.predict(model_frame[ctx.features])[0])
    return PredictTsaResponse(
        product="what_if_direct",
        model_id=ctx.run_id,
        family=ctx.family,
        tsa_dia=tsa_dia,
        disclaimer=(
            "Previsão sem histórico TSA — MAE holdout ~104 t/dia. "
            "Use /api/forecast para forecast operacional."
        ),
        metrics=HoldoutMetricsResponse(**ctx.metrics.as_dict()),
        field_origins=build_field_origins(resolved.origins),
        warnings=resolved.warnings,
    )

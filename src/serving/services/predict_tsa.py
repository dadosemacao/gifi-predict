from __future__ import annotations

from pathlib import Path

import pandas as pd

from serving.policy.tsa_loader import load_tsa_direct_context
from serving.schemas import HoldoutMetricsResponse, PredictTsaResponse
from serving.services.field_origins import build_field_origins
from serving.services.process_fields import process_dict_from_resolved
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
    )
    model_frame = process_dict_from_resolved(resolved.values)
    pipe, ctx = load_tsa_direct_context(
        repo_root, models_root=models_root, run_id=run_id
    )
    frame = pd.DataFrame([model_frame])
    missing = [c for c in ctx.features if c not in frame.columns]
    if missing:
        raise ValueError(f"features ausentes após resolução: {missing}")
    tsa_dia = float(pipe.predict(frame[ctx.features])[0])
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

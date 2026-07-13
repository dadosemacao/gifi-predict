from __future__ import annotations

from pathlib import Path

from serving.policy.forecast_loader import load_forecast_context
from serving.schemas import FieldOriginsResponse, ForecastResponse, HoldoutMetricsResponse
from serving.services.field_origins import build_field_origins
from serving.services.process_fields import process_dict_from_resolved
from serving.services.resolve_process_fields import resolve_process_fields
from simulation.forecast.predictor import predict_tsa


def run_forecast(
    body: dict,
    *,
    repo_root: Path,
    models_root: Path | None = None,
    run_id: str | None = None,
) -> ForecastResponse:
    tsa_history = [float(v) for v in body["tsa_history"]]
    resolved = resolve_process_fields(
        body,
        repo_root=repo_root,
    )
    model_frame = process_dict_from_resolved(resolved.values)
    artifact, ctx = load_forecast_context(
        repo_root, models_root=models_root, run_id=run_id
    )
    result = predict_tsa(artifact, model_frame, tsa_history)
    return ForecastResponse(
        product="forecast_operacional",
        model_id=ctx.run_id,
        family=ctx.family,
        anchor_name=result["anchor_name"],
        tsa_dia=result["tsa_dia"],
        tsa_dia_lo=result["tsa_dia_lo"],
        tsa_dia_hi=result["tsa_dia_hi"],
        anchor=result["anchor"],
        residual=result["residual"],
        baselines=result["baselines"],
        metrics=HoldoutMetricsResponse(**ctx.metrics.as_dict()),
        field_origins=build_field_origins(resolved.origins),
        warnings=resolved.warnings,
    )

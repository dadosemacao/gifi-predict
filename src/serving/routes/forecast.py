from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from serving.config import ServingSettings
from serving.policy.forecast_loader import load_forecast_context
from serving.schemas import ForecastRequest, ForecastResponse, ForecastStatusResponse
from serving.services.forecast import run_forecast

router = APIRouter(tags=["forecast"])


@router.get("/api/forecast/status", response_model=ForecastStatusResponse)
def forecast_status(
    run_id: str | None = Query(default=None),
) -> ForecastStatusResponse:
    settings = ServingSettings.from_yaml()
    try:
        _, ctx = load_forecast_context(
            settings.repo_root,
            models_root=settings.forecast_models_root,
            run_id=run_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ForecastStatusResponse(
        run_id=ctx.run_id,
        family=ctx.family,
        anchor=ctx.anchor,
        product="forecast_operacional",
        holdout_mae=ctx.holdout_mae,
        holdout_r2=ctx.holdout_r2,
        interval_80_coverage=ctx.interval_coverage,
        artifact_path=str(ctx.artifact_path),
    )


@router.post("/api/forecast", response_model=ForecastResponse)
def forecast(
    body: ForecastRequest,
    run_id: str | None = Query(default=None),
) -> ForecastResponse:
    settings = ServingSettings.from_yaml()
    try:
        return run_forecast(
            body.model_dump(),
            repo_root=settings.repo_root,
            models_root=settings.forecast_models_root,
            run_id=run_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

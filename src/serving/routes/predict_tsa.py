from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from serving.config import ServingSettings
from serving.policy.tsa_loader import load_tsa_direct_context
from serving.schemas import PredictTsaRequest, PredictTsaResponse, PredictTsaStatusResponse
from serving.services.predict_tsa import run_predict_tsa

router = APIRouter(tags=["predict-tsa"])


@router.get("/api/predict-tsa/status", response_model=PredictTsaStatusResponse)
def predict_tsa_status(
    run_id: str | None = Query(default=None),
) -> PredictTsaStatusResponse:
    settings = ServingSettings.from_yaml()
    try:
        _, ctx = load_tsa_direct_context(
            settings.repo_root,
            models_root=settings.forecast_models_root,
            run_id=run_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PredictTsaStatusResponse(
        run_id=ctx.run_id,
        family=ctx.family,
        product="what_if_direct",
        holdout_mae=ctx.holdout_mae,
        holdout_r2=ctx.holdout_r2,
        interval_80_coverage=ctx.metrics.interval_80_coverage,
        artifact_path=str(ctx.artifact_path),
        features=ctx.features,
    )


@router.post("/api/predict-tsa", response_model=PredictTsaResponse)
def predict_tsa(
    body: PredictTsaRequest,
    run_id: str | None = Query(default=None),
) -> PredictTsaResponse:
    settings = ServingSettings.from_yaml()
    try:
        return run_predict_tsa(
            body.model_dump(),
            repo_root=settings.repo_root,
            models_root=settings.forecast_models_root,
            run_id=run_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

from __future__ import annotations

from fastapi import APIRouter

from serving.policy.release import load_release_context
from serving.schemas import ReleaseStatusResponse

router = APIRouter(tags=["release"])


@router.get("/api/release-status", response_model=ReleaseStatusResponse)
def release_status(run_id: str | None = None) -> ReleaseStatusResponse:
    ctx = load_release_context(run_id)
    return ReleaseStatusResponse(
        run_id=ctx.run_id,
        release_ok=ctx.release_ok,
        demo_mode=ctx.demo_mode,
        l2_dataset_version=ctx.l2_dataset_version,
        mae_tsa_holdout=ctx.mae_tsa_holdout,
        champions=ctx.champions,
        matriz_a_ok=ctx.matriz_a_ok,
        matriz_b_ok=ctx.matriz_b_ok,
        matriz_c_ok=ctx.matriz_c_ok,
    )

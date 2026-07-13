from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, UploadFile

from serving.config import ServingSettings
from serving.policy.release import assert_simulate_allowed, load_release_context
from serving.schemas import InferenceResponse, ValidateResponse
from serving.services.simulate import run_simulate_upload
from serving.services.validate import run_validate_upload

router = APIRouter(tags=["scenario"])


@router.post("/api/scenario/validate", response_model=ValidateResponse)
async def validate_scenario(
    file: Annotated[UploadFile, File()],
    mode: Annotated[Literal["A", "B"], Form()] = "A",
) -> ValidateResponse:
    return await run_validate_upload(file, mode=mode)


@router.post("/api/simulate", response_model=InferenceResponse)
async def simulate(
    file: Annotated[UploadFile, File()],
    mode: Annotated[Literal["A", "B"], Form()] = "A",
    demo: Annotated[bool, Form()] = True,
    run_id: Annotated[str | None, Form()] = None,
) -> InferenceResponse:
    ctx = load_release_context(run_id)
    assert_simulate_allowed(ctx, demo_requested=demo)
    settings = ServingSettings.from_yaml()
    prefix = settings.ephemeral_prefix.rstrip("-")
    cenario_id = f"{prefix}-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (file.filename or "upload.csv")
        path.write_bytes(await file.read())
        return run_simulate_upload(
            path,
            cenario_id=cenario_id,
            mode=mode,
            release_ctx=ctx,
            demo=demo,
        )

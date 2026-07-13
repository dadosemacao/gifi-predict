from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from ingest.config import IngestSettings
from ingest.online.validator import validate_scenario_file
from serving.errors import ensure_supported_upload, validation_errors_to_http
from serving.schemas import ValidateResponse


def _check_mode_column(df: pd.DataFrame, mode: str) -> list[str]:
    if "modo" not in df.columns:
        return []
    expected = mode.upper()
    errors: list[str] = []
    for idx, row in df.iterrows():
        row_mode = str(row.get("modo", "")).upper()
        if row_mode and row_mode != expected:
            errors.append(f"row {idx}: modo mismatch (expected {expected}, got {row_mode})")
    return errors


async def run_validate_upload(file: UploadFile, *, mode: str) -> ValidateResponse:
    ensure_supported_upload(file)
    raw = await file.read()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / (file.filename or "upload.csv")
        path.write_bytes(raw)
        settings = IngestSettings.from_yaml()
        result = validate_scenario_file(path, "validate-online", settings)
        if result.get("ok") and "frame" in result:
            mode_errors = _check_mode_column(result["frame"], mode)
            if mode_errors:
                return ValidateResponse(
                    ok=False,
                    signal="INGEST_SCENARIO_REJECT",
                    errors=mode_errors,
                    sla_ms=result.get("sla_ms"),
                )
        if not result.get("ok"):
            errors = result.get("errors", ["validation failed"])
            if isinstance(errors, str):
                errors = [errors]
            return ValidateResponse(
                ok=False,
                signal=result.get("signal", "INGEST_SCENARIO_REJECT"),
                errors=list(errors),
                sla_ms=result.get("sla_ms"),
            )
        return ValidateResponse(
            ok=True,
            row_count=result.get("row_count"),
            sla_ms=result.get("sla_ms"),
        )


def validate_upload_path(path: Path, *, mode: str, settings: IngestSettings) -> ValidateResponse:
    result = validate_scenario_file(path, "validate-online", settings)
    if result.get("ok") and "frame" in result:
        mode_errors = _check_mode_column(result["frame"], mode)
        if mode_errors:
            raise validation_errors_to_http(mode_errors)
    if not result.get("ok"):
        errors = result.get("errors", ["validation failed"])
        if isinstance(errors, str):
            errors = [errors]
        raise validation_errors_to_http([str(e) for e in errors])
    return ValidateResponse(
        ok=True,
        row_count=result.get("row_count"),
        sla_ms=result.get("sla_ms"),
    )

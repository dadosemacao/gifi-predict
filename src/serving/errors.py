from __future__ import annotations

from fastapi import HTTPException, UploadFile


def ensure_supported_upload(file: UploadFile) -> None:
    name = (file.filename or "").lower()
    if not name.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=415,
            detail={"code": "unsupported_file", "message": "Use CSV ou XLSX."},
        )


def validation_errors_to_http(errors: list[str]) -> HTTPException:
    code = "INGEST_SCENARIO_REJECT"
    for err in errors:
        lower = err.lower()
        if "mix sum" in lower:
            code = "INGEST_MIX_FAIL"
            break
        if "modo a forbids" in lower:
            code = "mode_a_forbids_inject"
            break
        if "modo mismatch" in lower:
            code = "mode_mismatch"
            break
    return HTTPException(
        status_code=400,
        detail={"code": code, "errors": errors},
    )


def publish_error_to_http(exc: ValueError) -> HTTPException:
    errors = exc.args[0] if exc.args else ["validation failed"]
    if isinstance(errors, list):
        return validation_errors_to_http([str(e) for e in errors])
    return validation_errors_to_http([str(errors)])


def candidate_not_found(run_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "candidate_not_found", "run_id": run_id},
    )

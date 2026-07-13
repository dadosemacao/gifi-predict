from __future__ import annotations

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from serving.config import ServingSettings

router = APIRouter(tags=["static"])


@router.get("/api/template")
def download_template() -> PlainTextResponse:
    settings = ServingSettings.from_yaml()
    path = settings.template_file
    if not path.exists():
        raise HTTPException(status_code=404, detail="template_not_found")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    header = raw.get("example_header_csv", "").strip()
    if not header:
        raise HTTPException(status_code=404, detail="template_csv_not_defined")
    sample = header + "\nC-DEMO,1,A,8,60,1000,480,17,0.2,0.2,0.2,0.2,0.2\n"
    return PlainTextResponse(
        content=sample,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="template_cenario_v0.csv"'},
    )

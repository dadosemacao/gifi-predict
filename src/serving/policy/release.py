from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from serving.config import ServingSettings


@dataclass(frozen=True)
class ReleaseContext:
    run_id: str
    release_ok: bool
    demo_mode: bool
    l2_dataset_version: str
    mae_tsa_holdout: float | None
    champions: dict[str, str]
    report_path: Path
    matriz_a_ok: bool | None = None
    matriz_b_ok: bool | None = None
    matriz_c_ok: bool | None = None


def load_release_context(
    run_id: str | None = None,
    settings: ServingSettings | None = None,
) -> ReleaseContext:
    cfg = settings or ServingSettings.from_yaml()
    rid = run_id or cfg.default_run_id
    if not rid:
        raise HTTPException(
            status_code=503,
            detail={"code": "default_run_id_not_configured"},
        )
    report_path = cfg.reports_path / rid / "acceptance_report.json"
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "acceptance_report_not_found", "run_id": rid},
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ma = report.get("matriz_a", {})
    mb = report.get("matriz_b", {})
    mc = report.get("matriz_c", {})
    return ReleaseContext(
        run_id=rid,
        release_ok=bool(report.get("release_ok")),
        demo_mode=bool(report.get("demo_mode")),
        l2_dataset_version=str(report.get("l2_dataset_version", "")),
        mae_tsa_holdout=ma.get("mae_tsa_cascade"),
        champions=dict(report.get("l3_champions", {})),
        report_path=report_path,
        matriz_a_ok=ma.get("ok"),
        matriz_b_ok=mb.get("ok"),
        matriz_c_ok=mc.get("ok"),
    )


def assert_simulate_allowed(ctx: ReleaseContext, *, demo_requested: bool) -> None:
    if not demo_requested and not ctx.release_ok:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "production_bind_blocked",
                "release_ok": False,
                "demo_mode": ctx.demo_mode,
            },
        )

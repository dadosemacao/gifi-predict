from __future__ import annotations

from typing import Any

from acceptance.config import AcceptanceSettings
from acceptance.package.reporter import load_acceptance_report, render_summary_md


def run_report_pipeline(
    settings: AcceptanceSettings,
    *,
    run_id: str,
) -> dict[str, Any]:
    report = load_acceptance_report(settings.reports_path, run_id)
    summary = render_summary_md(report)
    return {
        "run_id": run_id,
        "release_ok": report.get("release_ok"),
        "demo_mode": report.get("demo_mode"),
        "summary": summary,
        "report": report,
    }

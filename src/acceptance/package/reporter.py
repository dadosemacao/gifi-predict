from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from acceptance.l3.loader import L3CandidateBundle
from acceptance.matrices.matriz_a import MatrizAResult
from acceptance.matrices.matriz_b import MatrizBResult
from acceptance.matrices.matriz_c import MatrizCResult
from acceptance.package.atomic_io import atomic_write_json
from acceptance.policy.gate import GateResult
from simulation.l2.loader import L2Bundle


def build_acceptance_report(
    *,
    run_id: str,
    bundle: L3CandidateBundle,
    l2: L2Bundle,
    matriz_a: MatrizAResult,
    matriz_b: MatrizBResult,
    matriz_c: MatrizCResult,
    gate: GateResult,
    durations_ms: dict[str, int] | None = None,
) -> dict[str, Any]:
    l2_info = bundle.manifest.get("l2", {})
    return {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "l3_candidate_dir": str(bundle.candidate_dir),
        "l2_dataset_version": l2.dataset_version,
        "l2_schema_version": l2.schema_version,
        "l2_source_hash": l2.source_hash,
        "l3_champions": bundle.champions,
        "l3_l2_dataset_version": l2_info.get("dataset_version"),
        "matriz_a": matriz_a.to_dict(),
        "matriz_b": matriz_b.to_dict(),
        "matriz_c": matriz_c.to_dict(),
        "release_ok": gate.release_ok,
        "production_bind": gate.production_bind,
        "demo_mode": gate.demo_mode,
        "durations_ms": durations_ms or {},
    }


def render_summary_md(report: dict[str, Any]) -> str:
    ma = report["matriz_a"]
    mb = report["matriz_b"]
    mc = report["matriz_c"]
    lines = [
        "# Acceptance Summary",
        "",
        f"- **run_id:** {report['run_id']}",
        f"- **release_ok:** {report['release_ok']}",
        f"- **demo_mode:** {report['demo_mode']}",
        "",
        "## Matriz A (Estatística)",
        f"- ok: {ma['ok']}",
        f"- MAE TSA cascade: {ma['mae_tsa_cascade']:.2f} (limit {ma['limit']})",
        "",
        "## Matriz B (Física)",
        f"- ok: {mb['ok']}",
        f"- failures: {', '.join(mb['failures']) if mb['failures'] else 'none'}",
        "",
        "## Matriz C (Explicabilidade)",
        f"- ok: {mc['ok']}",
        f"- failures: {', '.join(mc['failures']) if mc['failures'] else 'none'}",
        "",
    ]
    return "\n".join(lines)


def publish_report(
    reports_root: Path,
    run_id: str,
    report: dict[str, Any],
) -> Path:
    dest = reports_root / run_id
    dest.mkdir(parents=True, exist_ok=True)
    atomic_write_json(dest / "acceptance_report.json", report)
    atomic_write_json(dest / "matriz_a.json", report["matriz_a"])
    atomic_write_json(dest / "matriz_b_results.json", report["matriz_b"])
    atomic_write_json(dest / "matriz_c_detractors.json", report["matriz_c"])
    summary = render_summary_md(report)
    (dest / "acceptance_summary.md").write_text(summary, encoding="utf-8")
    return dest


def load_acceptance_report(reports_root: Path, run_id: str) -> dict[str, Any]:
    path = reports_root / run_id / "acceptance_report.json"
    if not path.exists():
        raise FileNotFoundError(f"acceptance_report.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

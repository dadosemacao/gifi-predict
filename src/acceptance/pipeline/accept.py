from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from acceptance.config import AcceptanceSettings
from acceptance.l3.guard import guard_l2_for_acceptance, guard_l3_integrity
from acceptance.l3.loader import load_l3_candidate
from acceptance.matrices.matriz_a import run_matriz_a
from acceptance.matrices.matriz_b import run_matriz_b
from acceptance.matrices.matriz_c import run_matriz_c
from acceptance.observability.logging import log_accept_event
from acceptance.package.champion import promote_champion
from acceptance.package.reporter import build_acceptance_report, publish_report
from acceptance.policy.gate import combine_gate
from acceptance.scenarios.loader import load_scenarios
from simulation.l2.loader import load_l2_bundle


def run_accept_pipeline(
    settings: AcceptanceSettings,
    *,
    run_id: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    log_id = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_file = settings.logs_path / f"accept_{log_id.replace(':', '-')}.jsonl"

    log_accept_event(run_id=run_id, event="accept_start", log_file=log_file)

    bundle = load_l3_candidate(settings.models_path, run_id)
    guard_l3_integrity(bundle)

    l2 = load_l2_bundle(settings.l2_path, max_retries=settings.max_retries)
    guard_l2_for_acceptance(l2.manifest)

    t_a = time.perf_counter()
    matriz_a = run_matriz_a(
        bundle,
        l2,
        mae_limit=settings.mae_limit,
        recompute=settings.recompute_matriz_a,
        db_proxy_factor=settings.db_proxy_factor,
    )
    dur_a = int((time.perf_counter() - t_a) * 1000)
    log_accept_event(
        run_id=run_id,
        event="matriz_a_done",
        log_file=log_file,
        ok=matriz_a.ok,
        duration_ms=dur_a,
    )

    scenario_specs = load_scenarios(settings.scenarios_path)

    t_b = time.perf_counter()
    matriz_b = run_matriz_b(
        bundle,
        scenario_specs,
        db_proxy_factor=settings.db_proxy_factor,
    )
    dur_b = int((time.perf_counter() - t_b) * 1000)
    log_accept_event(
        run_id=run_id,
        event="matriz_b_done",
        log_file=log_file,
        ok=matriz_b.ok,
        duration_ms=dur_b,
    )

    t_c = time.perf_counter()
    matriz_c = run_matriz_c(
        bundle,
        scenario_specs,
        required_in_top3=settings.matriz_c_required,
        db_proxy_factor=settings.db_proxy_factor,
        holdout=l2.holdout,
    )
    dur_c = int((time.perf_counter() - t_c) * 1000)
    log_accept_event(
        run_id=run_id,
        event="matriz_c_done",
        log_file=log_file,
        ok=matriz_c.ok,
        duration_ms=dur_c,
    )

    gate = combine_gate(matriz_a, matriz_b, matriz_c)
    durations = {"matriz_a": dur_a, "matriz_b": dur_b, "matriz_c": dur_c}

    report = build_acceptance_report(
        run_id=run_id,
        bundle=bundle,
        l2=l2,
        matriz_a=matriz_a,
        matriz_b=matriz_b,
        matriz_c=matriz_c,
        gate=gate,
        durations_ms=durations,
    )
    report_dir = publish_report(settings.reports_path, run_id, report)

    champion_dir = None
    if gate.release_ok:
        champion_dir = promote_champion(
            settings.models_path,
            run_id,
            report,
            lock_timeout_s=float(settings.lock_timeout_s),
        )

    total_ms = int((time.perf_counter() - started) * 1000)
    log_accept_event(
        run_id=run_id,
        event="accept_end",
        log_file=log_file,
        release_ok=gate.release_ok,
        duration_ms=total_ms,
    )

    return {
        "run_id": run_id,
        "release_ok": gate.release_ok,
        "demo_mode": gate.demo_mode,
        "production_bind": gate.production_bind,
        "report_dir": str(report_dir),
        "champion_dir": str(champion_dir) if champion_dir else None,
        "matriz_a": matriz_a.ok,
        "matriz_b": matriz_b.ok,
        "matriz_c": matriz_c.ok,
    }

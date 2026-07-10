from __future__ import annotations

import json

from acceptance.l3.loader import load_l3_candidate
from acceptance.matrices.matriz_a import MatrizAResult
from acceptance.matrices.matriz_b import MatrizBResult
from acceptance.matrices.matriz_c import MatrizCResult
from acceptance.package.champion import promote_champion
from acceptance.package.reporter import build_acceptance_report
from acceptance.policy.gate import combine_gate


def test_demo_mode_when_gate_fails():
    gate = combine_gate(
        MatrizAResult(False, 95, 56, 1, 1, 95, "t", {}),
        MatrizBResult(True, [], []),
        MatrizCResult(True, [], []),
    )
    assert gate.demo_mode
    assert not gate.production_bind


def test_champion_promotion_and_last_good(acceptance_settings, monotonic_run_id):
    bundle = load_l3_candidate(acceptance_settings.models_path, monotonic_run_id)
    ma = MatrizAResult(True, 30, 56, 0.5, 0.5, 30, "test", {})
    mb = MatrizBResult(True, [], [])
    mc = MatrizCResult(True, [], [])
    gate = combine_gate(ma, mb, mc)
    report = build_acceptance_report(
        run_id=monotonic_run_id,
        bundle=bundle,
        l2=type(
            "L2",
            (),
            {
                "dataset_version": "test",
                "schema_version": "1.0.0",
                "source_hash": "sha256:test",
            },
        )(),
        matriz_a=ma,
        matriz_b=mb,
        matriz_c=mc,
        gate=gate,
    )
    promote_champion(acceptance_settings.models_path, monotonic_run_id, report)
    champion_ptr = acceptance_settings.models_path / "current_champion.json"
    assert champion_ptr.exists()

    fail_report = dict(report)
    fail_report["release_ok"] = False
    fail_report["matriz_a"] = ma.to_dict()
    fail_report["matriz_a"]["ok"] = False
    ptr_before = json.loads(champion_ptr.read_text(encoding="utf-8"))
    assert ptr_before["run_id"] == monotonic_run_id

    champion_dir = acceptance_settings.models_path / "champion" / monotonic_run_id
    assert champion_dir.is_dir()
    assert (champion_dir / "champion_manifest.json").exists()

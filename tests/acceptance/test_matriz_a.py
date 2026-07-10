from __future__ import annotations

from acceptance.matrices.matriz_a import MatrizAResult
from acceptance.matrices.matriz_b import MatrizBResult
from acceptance.matrices.matriz_c import MatrizCResult
from acceptance.policy.gate import combine_gate


def test_matriz_a_passes_below_limit():
    ma = MatrizAResult(
        ok=True,
        mae_tsa_cascade=40.0,
        limit=56.0,
        mae_extrativos=1.0,
        mae_carga=1.0,
        mae_tsa_isolated=40.0,
        source="test",
        details={},
    )
    assert ma.ok


def test_matriz_a_fails_above_limit():
    ma = MatrizAResult(
        ok=False,
        mae_tsa_cascade=94.79,
        limit=56.0,
        mae_extrativos=1.0,
        mae_carga=1.0,
        mae_tsa_isolated=94.0,
        source="test",
        details={},
    )
    assert not ma.ok


def test_combine_gate_all_pass():
    ma = MatrizAResult(True, 30, 56, 1, 1, 30, "t", {})
    mb = MatrizBResult(True, [], [])
    mc = MatrizCResult(True, [], [])
    gate = combine_gate(ma, mb, mc)
    assert gate.release_ok
    assert gate.production_bind
    assert not gate.demo_mode


def test_combine_gate_partial_fail():
    ma = MatrizAResult(True, 30, 56, 1, 1, 30, "t", {})
    mb = MatrizBResult(False, [], ["TM-01"])
    mc = MatrizCResult(True, [], [])
    gate = combine_gate(ma, mb, mc)
    assert not gate.release_ok
    assert gate.demo_mode

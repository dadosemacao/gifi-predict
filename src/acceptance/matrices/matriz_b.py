from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acceptance.l3.loader import L3CandidateBundle
from acceptance.runner.inference import predict_tsa, predict_tsa_sequence
from acceptance.scenarios.loader import ScenarioSpec, tc_scenarios, tm_scenarios


def check_direction(
    baseline_tsa: float,
    stressed_tsa: float,
    direction: str,
) -> bool:
    if direction == "down":
        return stressed_tsa < baseline_tsa
    if direction == "up":
        return stressed_tsa > baseline_tsa
    if direction == "non_up":
        return stressed_tsa <= baseline_tsa
    raise ValueError(f"unknown direction: {direction}")


def check_monotonic_sequence(tsa_values: list[float], expect: str) -> bool:
    if len(tsa_values) < 2:
        return True
    if expect == "non_up":
        return all(tsa_values[i] >= tsa_values[i + 1] for i in range(len(tsa_values) - 1))
    if expect == "down":
        return all(tsa_values[i] > tsa_values[i + 1] for i in range(len(tsa_values) - 1))
    raise ValueError(f"unknown expect: {expect}")


@dataclass(frozen=True)
class ScenarioRunResult:
    id: str
    passed: bool
    baseline_tsa: float | None
    stressed_tsa: float | None
    delta: float | None
    direction: str | None
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "passed": self.passed,
            "baseline_tsa": self.baseline_tsa,
            "stressed_tsa": self.stressed_tsa,
            "delta": self.delta,
            "direction": self.direction,
            "details": self.details,
        }


@dataclass(frozen=True)
class MatrizBResult:
    ok: bool
    results: list[ScenarioRunResult]
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "failures": self.failures,
            "results": [r.to_dict() for r in self.results],
        }


def _resolve_baseline(
    spec: ScenarioSpec,
    specs: dict[str, ScenarioSpec],
) -> ScenarioSpec | None:
    baseline_id = spec.baseline_id or spec.expect.get("baseline_id")
    if baseline_id:
        return specs.get(baseline_id)
    return None


def run_matriz_b(
    bundle: L3CandidateBundle,
    specs: dict[str, ScenarioSpec],
    *,
    db_proxy_factor: float,
) -> MatrizBResult:
    results: list[ScenarioRunResult] = []
    failures: list[str] = []

    for spec in tc_scenarios(specs):
        if spec.scenario_type == "feature_check":
            results.append(
                ScenarioRunResult(
                    id=spec.id,
                    passed=True,
                    baseline_tsa=None,
                    stressed_tsa=None,
                    delta=None,
                    direction=None,
                    details={"note": "feature_check deferred to ingest/L2"},
                )
            )
            continue

        baseline_spec = _resolve_baseline(spec, specs)
        direction = spec.expect.get("direction", "down")
        stressed_tsa = predict_tsa(
            spec.inputs,
            mode=spec.mode,
            pipes=bundle.pipes,
            feature_cols=bundle.feature_cols,
            db_proxy_factor=db_proxy_factor,
        )
        baseline_tsa: float | None = None
        passed = True
        if baseline_spec is not None:
            baseline_tsa = predict_tsa(
                baseline_spec.inputs,
                mode=baseline_spec.mode,
                pipes=bundle.pipes,
                feature_cols=bundle.feature_cols,
                db_proxy_factor=db_proxy_factor,
            )
            passed = check_direction(baseline_tsa, stressed_tsa, direction)
        elif spec.expect.get("type") == "threshold":
            field = spec.expect.get("field", "Carga_Alcalina")
            op = spec.expect.get("op", ">")
            threshold = float(spec.expect.get("value", 0))
            value = float(spec.inputs.get(field, stressed_tsa))
            if op == ">":
                passed = value > threshold
            elif op == "<":
                passed = value < threshold
            baseline_tsa = value

        if not passed:
            failures.append(spec.id)
        delta = (
            (stressed_tsa - baseline_tsa)
            if baseline_tsa is not None
            else None
        )
        results.append(
            ScenarioRunResult(
                id=spec.id,
                passed=passed,
                baseline_tsa=baseline_tsa,
                stressed_tsa=stressed_tsa,
                delta=delta,
                direction=direction,
                details={"mode": spec.mode},
            )
        )

    for tm in tm_scenarios(specs):
        anchor_id = tm.anchor or "anchor_mixed"
        anchor = specs.get(anchor_id)
        if anchor is None or tm.variable is None or tm.sequence is None:
            failures.append(tm.id)
            results.append(
                ScenarioRunResult(
                    id=tm.id,
                    passed=False,
                    baseline_tsa=None,
                    stressed_tsa=None,
                    delta=None,
                    direction=tm.expect.get("direction", "non_up"),
                    details={"error": f"anchor {anchor_id} missing"},
                )
            )
            continue
        expect = tm.expect.get("direction") or tm.expect.get("expect") or "non_up"
        tsa_seq = predict_tsa_sequence(
            anchor.inputs,
            mode=tm.mode,
            variable=tm.variable,
            sequence=tm.sequence,
            pipes=bundle.pipes,
            feature_cols=bundle.feature_cols,
            db_proxy_factor=db_proxy_factor,
        )
        passed = check_monotonic_sequence(tsa_seq, expect)
        if not passed:
            failures.append(tm.id)
        results.append(
            ScenarioRunResult(
                id=tm.id,
                passed=passed,
                baseline_tsa=tsa_seq[0] if tsa_seq else None,
                stressed_tsa=tsa_seq[-1] if tsa_seq else None,
                delta=(tsa_seq[-1] - tsa_seq[0]) if len(tsa_seq) >= 2 else None,
                direction=expect,
                details={"sequence_tsa": tsa_seq, "variable": tm.variable},
            )
        )

    return MatrizBResult(ok=len(failures) == 0, results=results, failures=failures)

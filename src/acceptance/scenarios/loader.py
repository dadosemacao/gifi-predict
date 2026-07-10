from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ScenarioSpec:
    id: str
    scenario_type: str
    mode: str
    description: str = ""
    normative_ref: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    anchor: str | None = None
    variable: str | None = None
    sequence: list[float] | None = None
    baseline_id: str | None = None


def _parse_spec(raw: dict[str, Any]) -> ScenarioSpec:
    expect = raw.get("expect") or {}
    if isinstance(expect, str):
        expect = {"direction": expect}
    baseline_id = expect.get("baseline_id") or raw.get("baseline_id")
    return ScenarioSpec(
        id=str(raw["id"]),
        scenario_type=str(raw.get("type", "compare_baseline")),
        mode=str(raw.get("mode", "B")).upper(),
        description=str(raw.get("description", "")),
        normative_ref=str(raw.get("normative_ref", "")),
        inputs=dict(raw.get("inputs") or {}),
        expect=dict(expect),
        anchor=raw.get("anchor"),
        variable=raw.get("variable"),
        sequence=list(raw["sequence"]) if raw.get("sequence") else None,
        baseline_id=baseline_id,
    )


def load_scenarios(scenarios_dir: Path) -> dict[str, ScenarioSpec]:
    specs: dict[str, ScenarioSpec] = {}
    if not scenarios_dir.is_dir():
        return specs
    for path in sorted(scenarios_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if "id" not in raw:
            continue
        spec = _parse_spec(raw)
        specs[spec.id] = spec
    return specs


def tc_scenarios(specs: dict[str, ScenarioSpec]) -> list[ScenarioSpec]:
    return [
        s
        for s in specs.values()
        if s.id.startswith("TC-")
        and s.scenario_type in ("compare_baseline", "threshold", "feature_check")
    ]


def tm_scenarios(specs: dict[str, ScenarioSpec]) -> list[ScenarioSpec]:
    return [s for s in specs.values() if s.id.startswith("TM-")]


def matriz_c_scenarios(specs: dict[str, ScenarioSpec]) -> list[ScenarioSpec]:
    return [s for s in specs.values() if s.scenario_type == "matriz_c"]

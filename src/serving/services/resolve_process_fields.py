from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from serving.policy.extr_imputer_loader import load_extr_serving_imputer
from simulation.process_specs import (
    AUX_API_FIELDS,
    MANDATORY_API_FIELDS,
    PROCESS_API_TO_COLUMN,
    encode_prod_alcali_class,
)

Origin = Literal["medido", "proxy", "estimado"]

REQUIRED_API_FIELDS: tuple[str, ...] = tuple(PROCESS_API_TO_COLUMN.keys())
AUX_INPUT_FIELDS = AUX_API_FIELDS


@dataclass
class ResolvedProcess:
    values: dict[str, float]
    origins: dict[str, Origin]
    warnings: list[str] = field(default_factory=list)


def resolve_process_fields(
    body: dict[str, Any],
    *,
    repo_root,
    enable_tier_b: bool = True,
) -> ResolvedProcess:
    """Preenche campos ausentes (Tier A proxy + Tier B estimado)."""
    data: dict[str, float | None] = {}
    origins: dict[str, Origin] = {}
    warnings: list[str] = []

    for key in (*REQUIRED_API_FIELDS, *AUX_INPUT_FIELDS):
        raw = body.get(key)
        if raw is None:
            continue
        if key == "prod_alcali_class":
            data[key] = encode_prod_alcali_class(raw)
        else:
            data[key] = float(raw)
        if key in REQUIRED_API_FIELDS:
            origins[key] = "medido"

    _validate_mandatory(data)

    _resolve_pct_ab(data, origins, warnings)
    _resolve_pct_dmg(data, origins, warnings)
    _resolve_vmi_flags(data, origins, warnings)

    if enable_tier_b and data.get("extrativo_at") is None:
        _estimate_extrativo_at(data, origins, warnings, repo_root=repo_root)

    missing = [k for k in REQUIRED_API_FIELDS if data.get(k) is None]
    if missing:
        raise ValueError(
            "campos ausentes após resolução: "
            + ", ".join(missing)
            + ". Informe o valor ou insumos para derivação (ex.: vmi, pct_a..pct_mg)."
        )

    values = {k: float(data[k]) for k in REQUIRED_API_FIELDS if data[k] is not None}
    return ResolvedProcess(values=values, origins=origins, warnings=warnings)


def _validate_mandatory(data: dict[str, float | None]) -> None:
    missing = [k for k in MANDATORY_API_FIELDS if data.get(k) is None]
    if missing:
        raise ValueError(f"campos obrigatórios ausentes: {', '.join(missing)}")


def _resolve_pct_ab(
    data: dict[str, float | None],
    origins: dict[str, Origin],
    warnings: list[str],
) -> None:
    if data.get("pct_ab") is not None:
        return
    a = data.get("pct_a")
    b = data.get("pct_b")
    if a is None or b is None:
        return
    data["pct_ab"] = float(a) + float(b)
    origins["pct_ab"] = "proxy"
    warnings.append("pct_ab derivado de pct_a + pct_b")


def _resolve_pct_dmg(
    data: dict[str, float | None],
    origins: dict[str, Origin],
    warnings: list[str],
) -> None:
    if data.get("pct_dmg") is not None:
        return
    d = data.get("pct_d")
    mg = data.get("pct_mg")
    if d is None or mg is None:
        return
    data["pct_dmg"] = float(d) + float(mg)
    origins["pct_dmg"] = "proxy"
    warnings.append("pct_dmg derivado de pct_d + pct_mg")


def _resolve_vmi_flags(
    data: dict[str, float | None],
    origins: dict[str, Origin],
    warnings: list[str],
) -> None:
    if all(data.get(k) is not None for k in ("vmi_le_021", "vmi_021_025", "vmi_gt_025")):
        return
    vmi = data.get("vmi")
    if vmi is None:
        return
    v = float(vmi)
    data["vmi_le_021"] = 1.0 if v <= 0.21 else 0.0
    data["vmi_021_025"] = 1.0 if 0.21 < v <= 0.25 else 0.0
    data["vmi_gt_025"] = 1.0 if v > 0.25 else 0.0
    for key in ("vmi_le_021", "vmi_021_025", "vmi_gt_025"):
        origins[key] = "proxy"
    warnings.append("flags VMI derivadas de vmi contínuo")


def _estimate_extrativo_at(
    data: dict[str, float | None],
    origins: dict[str, Origin],
    warnings: list[str],
    *,
    repo_root,
) -> None:
    needed = ("pct_ab", "pct_c", "pct_dmg", "idade")
    if any(data.get(k) is None for k in needed):
        return

    model, meta = load_extr_serving_imputer(str(repo_root))
    features = meta.get("features", ["pct_AB", "pct_C", "pct_DMG", "Idade"])
    row = {
        "pct_AB": float(data["pct_ab"]),  # type: ignore[arg-type]
        "pct_C": float(data["pct_c"]),  # type: ignore[arg-type]
        "pct_DMG": float(data["pct_dmg"]),  # type: ignore[arg-type]
        "Idade": float(data["idade"]),  # type: ignore[arg-type]
    }
    frame = pd.DataFrame([row])
    pred = float(model.predict(frame[features])[0])
    lo = float(meta.get("range_min", 1.0))
    hi = float(meta.get("range_max", 3.5))
    y_min = float(meta.get("y_min", lo))
    y_max = float(meta.get("y_max", hi))
    pred = max(lo, min(hi, max(y_min, min(y_max, pred))))
    data["extrativo_at"] = pred
    origins["extrativo_at"] = "estimado"
    warnings.append("extrativo_at estimado via imputer serving (mix + idade)")

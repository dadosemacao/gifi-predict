from __future__ import annotations

import math

import pandas as pd

MIX_PCTS = ["pct_A", "pct_B", "pct_C", "pct_D", "pct_MG"]
DOM_SITES = ["A", "B", "C", "D", "MG"]


def _entropy(row: pd.Series) -> float:
    values = [row[c] for c in MIX_PCTS if c in row and pd.notna(row[c]) and row[c] > 0]
    if not values:
        return 0.0
    total = sum(values)
    probs = [v / total for v in values]
    return float(-sum(p * math.log(p) for p in probs))


def _hhi(row: pd.Series) -> float:
    values = [row.get(c, 0.0) or 0.0 for c in MIX_PCTS]
    return float(sum(v * v for v in values))


def derive_mix_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if all(c in out.columns for c in MIX_PCTS):
        out["pct_AB"] = out["pct_A"] + out["pct_B"]
        out["pct_DMG"] = out["pct_D"] + out["pct_MG"]
        out["pct_ABC"] = out["pct_A"] + out["pct_B"] + out["pct_C"]
        out["pct_CDMG"] = out["pct_C"] + out["pct_D"] + out["pct_MG"]
        out["mix_entropy"] = out.apply(_entropy, axis=1)
        out["mix_hhi"] = out.apply(_hhi, axis=1)
        dom_idx = out[MIX_PCTS].to_numpy().argmax(axis=1)
        for i, site in enumerate(DOM_SITES):
            out[f"dom_{site}"] = (dom_idx == i).astype(int)
    return out


def derive_vmi_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "VMI" not in out.columns:
        return out
    out["vmi_le_021"] = (out["VMI"] <= 0.21).astype(int)
    out["vmi_021_025"] = ((out["VMI"] > 0.21) & (out["VMI"] <= 0.25)).astype(int)
    out["vmi_gt_025"] = (out["VMI"] > 0.25).astype(int)
    return out

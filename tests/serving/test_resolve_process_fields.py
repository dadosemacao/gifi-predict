from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from serving.services.resolve_process_fields import resolve_process_fields


def _full_row(repo_root: Path) -> dict:
    row = pd.read_csv(repo_root / "base" / "primeira_base.csv").iloc[0]
    return {
        "carga_alcalina": float(row["Carga_Alcalina"]),
        "kappa": float(row["Kappa"]),
        "db_sgf": float(row["DB_SGF"]),
        "db_lab": float(row["DB_LAB"]),
        "secura_pct": float(row["Secura_pct"]),
        "casca_pct": float(row["Casca_pct"]),
        "extrativo_total": float(row["Extrativo_Total"]),
        "extrativo_at": float(row["Extrativo_AT"]),
        "extrativo_sgf": float(row["Extrativo_SGF"]),
        "tpc": float(row["TPC"]),
        "idade": float(row["Idade"]),
        "vmi_le_021": float(row["vmi_le_021"]),
        "vmi_021_025": float(row["vmi_021_025"]),
        "vmi_gt_025": float(row["vmi_gt_025"]),
        "pct_ab": float(row["pct_AB"]),
        "pct_c": float(row["pct_C"]),
        "pct_dmg": float(row["pct_DMG"]),
    }


def test_tier_a_db_lab_proxy(repo_root: Path) -> None:
    body = _full_row(repo_root)
    db_lab = body.pop("db_lab")
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.origins["db_lab"] == "proxy"
    assert resolved.values["db_lab"] == pytest.approx(body["db_sgf"] * 0.985, rel=1e-3)
    assert resolved.values["db_lab"] != db_lab


def test_tier_a_vmi_from_continuous(repo_root: Path) -> None:
    body = _full_row(repo_root)
    body.pop("vmi_le_021")
    body.pop("vmi_021_025")
    body.pop("vmi_gt_025")
    body["vmi"] = 0.30
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.origins["vmi_gt_025"] == "proxy"
    assert resolved.values["vmi_gt_025"] == 1.0
    assert resolved.values["vmi_le_021"] == 0.0


def test_tier_b_extrativo_at_estimated(repo_root: Path) -> None:
    body = _full_row(repo_root)
    body.pop("extrativo_at")
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.origins["extrativo_at"] == "estimado"
    assert 1.0 <= resolved.values["extrativo_at"] <= 3.5
    assert any("extrativo_at estimado" in w for w in resolved.warnings)


def test_missing_after_resolution_raises(repo_root: Path) -> None:
    body = _full_row(repo_root)
    body.pop("pct_ab")
    body.pop("pct_c")
    body.pop("pct_dmg")
    with pytest.raises(ValueError, match="campos ausentes após resolução"):
        resolve_process_fields(body, repo_root=repo_root)

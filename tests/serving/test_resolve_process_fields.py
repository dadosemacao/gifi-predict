from __future__ import annotations

from pathlib import Path

import pytest

from serving.services.resolve_process_fields import resolve_process_fields


def test_tier_a_vmi_from_continuous(repo_root: Path, sample_process_payload: dict) -> None:
    body = dict(sample_process_payload)
    body.pop("vmi_le_021")
    body.pop("vmi_021_025")
    body.pop("vmi_gt_025")
    body["vmi"] = 0.30
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.origins["vmi_gt_025"] == "proxy"
    assert resolved.values["vmi_gt_025"] == 1.0
    assert resolved.values["vmi_le_021"] == 0.0


def test_tier_b_extrativo_at_estimated(repo_root: Path, sample_process_payload: dict) -> None:
    body = dict(sample_process_payload)
    body.pop("extrativo_at")
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.origins["extrativo_at"] == "estimado"
    assert 1.0 <= resolved.values["extrativo_at"] <= 3.5
    assert any("extrativo_at estimado" in w for w in resolved.warnings)


def test_prod_alcali_class_accepts_string(repo_root: Path, sample_process_payload: dict) -> None:
    body = dict(sample_process_payload)
    body["prod_alcali_class"] = "normal"
    resolved = resolve_process_fields(body, repo_root=repo_root)
    assert resolved.values["prod_alcali_class"] == 1.0


def test_missing_after_resolution_raises(repo_root: Path, sample_process_payload: dict) -> None:
    body = dict(sample_process_payload)
    body.pop("pct_ab")
    body.pop("pct_c")
    body.pop("pct_dmg")
    with pytest.raises(ValueError, match="campos ausentes após resolução"):
        resolve_process_fields(body, repo_root=repo_root)

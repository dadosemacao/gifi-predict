"""Unit tests for predict-tsa analytics helper.

Autor: Emerson Antônio
Data: 2026-07-13
"""

from __future__ import annotations

import pytest

from serving.services.predict_tsa_analytics import (
    SENSITIVITY_RANGES,
    build_analytics,
)


def test_build_analytics_rejects_bad_variable(repo_root, sample_process_payload: dict) -> None:
    from serving.policy.tsa_loader import load_tsa_direct_context
    from serving.services.resolve_process_fields import resolve_process_fields

    resolved = resolve_process_fields(sample_process_payload, repo_root=repo_root)
    pipe, ctx = load_tsa_direct_context(repo_root)
    with pytest.raises(ValueError, match="sensitivity_variable inválida"):
        build_analytics(
            pipe=pipe,
            features=ctx.features,
            resolved_api=resolved.values,
            tsa_dia=3400.0,
            sensitivity_variable="foo",
            sensitivity_steps=15,
        )


def test_build_analytics_rejects_bad_steps(repo_root, sample_process_payload: dict) -> None:
    from serving.policy.tsa_loader import load_tsa_direct_context
    from serving.services.resolve_process_fields import resolve_process_fields

    resolved = resolve_process_fields(sample_process_payload, repo_root=repo_root)
    pipe, ctx = load_tsa_direct_context(repo_root)
    with pytest.raises(ValueError, match="sensitivity_steps"):
        build_analytics(
            pipe=pipe,
            features=ctx.features,
            resolved_api=resolved.values,
            tsa_dia=3400.0,
            sensitivity_variable="db_sgf",
            sensitivity_steps=4,
        )


def test_build_analytics_sweep_and_top3(repo_root, sample_process_payload: dict) -> None:
    import pandas as pd

    from serving.policy.tsa_loader import load_tsa_direct_context
    from serving.services.process_fields import process_dict_from_resolved
    from serving.services.resolve_process_fields import resolve_process_fields

    resolved = resolve_process_fields(sample_process_payload, repo_root=repo_root)
    pipe, ctx = load_tsa_direct_context(repo_root)
    frame = pd.DataFrame([process_dict_from_resolved(resolved.values)])
    tsa = float(pipe.predict(frame[ctx.features])[0])
    result = build_analytics(
        pipe=pipe,
        features=ctx.features,
        resolved_api=resolved.values,
        tsa_dia=tsa,
        sensitivity_variable="db_sgf",
        sensitivity_steps=15,
    )
    low, high = SENSITIVITY_RANGES["db_sgf"]
    assert len(result.sensitivity) == 15
    assert result.sensitivity[0]["value"] == pytest.approx(low)
    assert result.sensitivity[-1]["value"] == pytest.approx(high)
    assert len(result.detractors) == 3
    assert all(d["method"] == "local_ablation" for d in result.detractors)
    abs_deltas = [abs(float(d["delta_tsa"])) for d in result.detractors]
    assert abs_deltas == sorted(abs_deltas, reverse=True)

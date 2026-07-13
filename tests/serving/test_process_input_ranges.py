"""Validação das faixas oficiais de entrada do serving.

Autor: Emerson Antônio
Data: 2026-07-13
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from serving.schemas import ForecastRequest, PredictTsaRequest


def _valid_process_payload() -> dict[str, float | str]:
    return {
        "carga_alcalina": 19.0,
        "kappa": 16.5,
        "prod_alcali_class": 1,
        "db_sgf": 490.0,
        "casca_pct": 0.8,
        "extrativo_at": 1.9,
        "tpc": 65.0,
        "idade": 6.7,
        "vmi_le_021": 0.0,
        "vmi_021_025": 0.0,
        "vmi_gt_025": 1.0,
        "pct_ab": 0.65,
        "pct_c": 0.10,
        "pct_dmg": 0.25,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("carga_alcalina", 17.49),
        ("carga_alcalina", 21.01),
        ("kappa", 14.99),
        ("kappa", 18.51),
        ("db_sgf", 464.99),
        ("db_sgf", 515.01),
        ("casca_pct", 1.51),
        ("tpc", 44.99),
    ],
)
@pytest.mark.parametrize("request_model", [ForecastRequest, PredictTsaRequest])
def test_request_rejects_values_outside_official_ranges(
    field: str,
    value: float,
    request_model: type[ForecastRequest] | type[PredictTsaRequest],
) -> None:
    payload = _valid_process_payload()
    payload[field] = value
    if request_model is ForecastRequest:
        payload["tsa_history"] = [3450.0] * 7

    with pytest.raises(ValidationError) as exc_info:
        request_model.model_validate(payload)

    errors = exc_info.value.errors()
    assert any(error["loc"] == (field,) for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("carga_alcalina", 17.5),
        ("carga_alcalina", 21.0),
        ("kappa", 15.0),
        ("kappa", 18.5),
        ("db_sgf", 465.0),
        ("db_sgf", 515.0),
        ("casca_pct", 1.5),
        ("tpc", 45.0),
    ],
)
def test_official_range_boundaries_are_inclusive(field: str, value: float) -> None:
    payload = _valid_process_payload()
    payload[field] = value

    parsed = PredictTsaRequest.model_validate(payload)

    assert getattr(parsed, field) == value


def test_prod_alcali_class_accepts_string_label() -> None:
    payload = _valid_process_payload()
    payload["prod_alcali_class"] = "baixo"

    parsed = PredictTsaRequest.model_validate(payload)

    assert parsed.prod_alcali_class == 0.0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("idade", 11.0),
        ("pct_c", 0.35),
    ],
)
def test_fields_without_official_ranges_remain_unbounded(
    field: str,
    value: float,
) -> None:
    payload = _valid_process_payload()
    payload[field] = value

    parsed = PredictTsaRequest.model_validate(payload)

    assert getattr(parsed, field) == value


@pytest.mark.parametrize(
    ("endpoint", "invalid_field", "invalid_value"),
    [
        ("/api/forecast", "carga_alcalina", 21.01),
        ("/api/predict-tsa", "tpc", 44.99),
    ],
)
def test_api_returns_422_for_official_range_violation(
    client,
    endpoint: str,
    invalid_field: str,
    invalid_value: float,
) -> None:
    payload = _valid_process_payload()
    payload[invalid_field] = invalid_value
    if endpoint == "/api/forecast":
        payload["tsa_history"] = [3450.0] * 7

    response = client.post(endpoint, json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(error["loc"][-1] == invalid_field for error in detail)

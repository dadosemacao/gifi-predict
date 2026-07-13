from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HoldoutMetricsResponse(BaseModel):
    mae_holdout: float
    r2_holdout: float
    interval_80_coverage: float


class CurvePoint(BaseModel):
    label: str
    tsa_dia: float
    carga_alcalina: float
    extrativo_at: float


class DetractorOut(BaseModel):
    feature: str
    delta_tsa: float
    method: Literal["shap", "coef", "permutation"]


class InferenceResponse(BaseModel):
    mode: Literal["A", "B"]
    demo: bool
    gate_ok: bool
    model_id: str
    acceptance_run_id: str
    l2_dataset_version: str
    curves: list[CurvePoint]
    detractors: list[DetractorOut] = Field(max_length=3)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, float | None] = Field(default_factory=dict)


class ValidateResponse(BaseModel):
    ok: bool
    row_count: int | None = None
    sla_ms: int | None = None
    signal: str | None = None
    errors: list[str] = Field(default_factory=list)


class ReleaseStatusResponse(BaseModel):
    run_id: str
    release_ok: bool
    demo_mode: bool
    l2_dataset_version: str
    mae_tsa_holdout: float | None
    champions: dict[str, str]
    matriz_a_ok: bool | None = None
    matriz_b_ok: bool | None = None
    matriz_c_ok: bool | None = None


class ProcessVariablesInput(BaseModel):
    """Entrada parcial — campos ausentes podem ser resolvidos (Tier A/B)."""

    carga_alcalina: float = Field(
        ge=17.5,
        le=21.0,
        description="Carga alcalina em % Na₂O; faixa oficial aceitável: 17,5–21,0",
    )
    kappa: float = Field(
        ge=15.0,
        le=18.5,
        description="Índice Kappa; faixa oficial aceitável: 15,0–18,5",
    )
    db_sgf: float = Field(
        ge=465.0,
        le=515.0,
        description="Densidade básica SGF em kg/m³; faixa oficial aceitável: 465–515",
    )
    db_lab: float | None = None
    secura_pct: float
    casca_pct: float = Field(
        le=1.5,
        description="Percentual de casca; limite oficial máximo aceitável: 1,5%",
    )
    extrativo_total: float
    extrativo_at: float | None = None
    extrativo_sgf: float
    tpc: float = Field(
        ge=45.0,
        description="TPC em dias; valores abaixo de 45 representam madeira verde",
    )
    idade: float
    vmi_le_021: float | None = None
    vmi_021_025: float | None = None
    vmi_gt_025: float | None = None
    pct_ab: float | None = None
    pct_c: float | None = None
    pct_dmg: float | None = None
    vmi: float | None = Field(
        default=None,
        description="VMI contínuo; deriva flags vmi_* quando ausentes",
    )
    pct_a: float | None = None
    pct_b: float | None = None
    pct_d: float | None = None
    pct_mg: float | None = None


class FieldOriginsResponse(BaseModel):
    """Origem de cada campo após resolução."""

    carga_alcalina: Literal["medido", "proxy", "estimado"] | None = None
    kappa: Literal["medido", "proxy", "estimado"] | None = None
    db_sgf: Literal["medido", "proxy", "estimado"] | None = None
    db_lab: Literal["medido", "proxy", "estimado"] | None = None
    secura_pct: Literal["medido", "proxy", "estimado"] | None = None
    casca_pct: Literal["medido", "proxy", "estimado"] | None = None
    extrativo_total: Literal["medido", "proxy", "estimado"] | None = None
    extrativo_at: Literal["medido", "proxy", "estimado"] | None = None
    extrativo_sgf: Literal["medido", "proxy", "estimado"] | None = None
    tpc: Literal["medido", "proxy", "estimado"] | None = None
    idade: Literal["medido", "proxy", "estimado"] | None = None
    vmi_le_021: Literal["medido", "proxy", "estimado"] | None = None
    vmi_021_025: Literal["medido", "proxy", "estimado"] | None = None
    vmi_gt_025: Literal["medido", "proxy", "estimado"] | None = None
    pct_ab: Literal["medido", "proxy", "estimado"] | None = None
    pct_c: Literal["medido", "proxy", "estimado"] | None = None
    pct_dmg: Literal["medido", "proxy", "estimado"] | None = None


class ForecastRequest(ProcessVariablesInput):
    """Forecast operacional (Produto A) — próximo turno."""

    tsa_history: list[float] = Field(
        ...,
        min_length=7,
        description="Histórico TSA por turno, ordem cronológica (último = mais recente)",
    )


class PredictTsaRequest(ProcessVariablesInput):
    """What-if direto (Produto B) — TSA a partir só das variáveis de processo."""


class PredictTsaResponse(BaseModel):
    product: Literal["what_if_direct"]
    model_id: str
    family: str
    tsa_dia: float
    disclaimer: str
    metrics: HoldoutMetricsResponse
    field_origins: FieldOriginsResponse
    warnings: list[str] = Field(default_factory=list)


class PredictTsaStatusResponse(BaseModel):
    run_id: str
    family: str
    product: Literal["what_if_direct"]
    holdout_mae: float
    holdout_r2: float
    interval_80_coverage: float
    artifact_path: str
    features: list[str]


class ForecastResponse(BaseModel):
    product: Literal["forecast_operacional"]
    model_id: str
    family: str
    anchor_name: str
    tsa_dia: float
    tsa_dia_lo: float
    tsa_dia_hi: float
    anchor: float
    residual: float
    baselines: dict[str, float]
    metrics: HoldoutMetricsResponse
    field_origins: FieldOriginsResponse
    warnings: list[str] = Field(default_factory=list)


class ForecastStatusResponse(BaseModel):
    run_id: str
    family: str
    anchor: str
    product: Literal["forecast_operacional"]
    holdout_mae: float
    holdout_r2: float
    interval_80_coverage: float
    artifact_path: str

import type { FieldOrigins, HoldoutMetrics } from "@/types/forecast"

export type PredictTsaRequest = {
  carga_alcalina: number
  kappa: number
  prod_alcali_class: number | "baixo" | "normal"
  db_sgf: number
  casca_pct: number
  extrativo_at?: number
  tpc: number
  idade: number
  vmi_le_021?: number
  vmi_021_025?: number
  vmi_gt_025?: number
  pct_ab?: number
  pct_c?: number
  pct_dmg?: number
}

export type PredictTsaResponse = {
  product: "what_if_direct"
  model_id: string
  family: string
  tsa_dia: number
  disclaimer: string
  metrics: HoldoutMetrics
  field_origins: FieldOrigins
  warnings: string[]
}

export type PredictTsaStatus = {
  run_id: string
  family: string
  product: "what_if_direct"
  holdout_mae: number
  holdout_r2: number
  interval_80_coverage: number
  artifact_path: string
  features: string[]
}

export type PredictTsaStatusResponse = PredictTsaStatus

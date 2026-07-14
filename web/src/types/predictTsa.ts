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

export type SensitivityPoint = {
  value: number
  tsa_dia: number
}

export type LocalDetractor = {
  feature: string
  delta_tsa: number
  method: "local_ablation"
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
  sensitivity?: SensitivityPoint[]
  detractors?: LocalDetractor[]
  sensitivity_variable?: string
  sensitivity_steps?: number
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

export type PostPredictTsaOptions = {
  includeAnalytics?: boolean
  sensitivityVariable?: string
  sensitivitySteps?: number
  runId?: string
}

export const SENSITIVITY_VARIABLE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "db_sgf", label: "DB SGF" },
  { value: "carga_alcalina", label: "Carga alcalina" },
  { value: "kappa", label: "Kappa" },
  { value: "casca_pct", label: "% Casca" },
  { value: "tpc", label: "TPC" },
  { value: "extrativo_at", label: "Extrativo AT" },
  { value: "idade", label: "Idade" },
]

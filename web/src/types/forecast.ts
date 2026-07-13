export type HoldoutMetrics = {
  mae_holdout: number
  r2_holdout: number
  interval_80_coverage: number
}

export type FieldOrigin = "medido" | "proxy" | "estimado"

export type FieldOrigins = {
  carga_alcalina?: FieldOrigin
  kappa?: FieldOrigin
  prod_alcali_class?: FieldOrigin
  db_sgf?: FieldOrigin
  casca_pct?: FieldOrigin
  extrativo_at?: FieldOrigin
  tpc?: FieldOrigin
  idade?: FieldOrigin
  vmi_le_021?: FieldOrigin
  vmi_021_025?: FieldOrigin
  vmi_gt_025?: FieldOrigin
  pct_ab?: FieldOrigin
  pct_dmg?: FieldOrigin
}

export type ForecastResponse = {
  product: "forecast_operacional"
  model_id: string
  family: string
  anchor_name: string
  tsa_dia: number
  tsa_dia_lo: number
  tsa_dia_hi: number
  anchor: number
  residual: number
  baselines: Record<string, number>
  metrics: HoldoutMetrics
  field_origins: FieldOrigins
  warnings: string[]
}

export type ForecastStatus = {
  run_id: string
  family: string
  anchor: string
  product: "forecast_operacional"
  holdout_mae: number
  holdout_r2: number
  interval_80_coverage: number
  artifact_path: string
}

export type ForecastRequest = {
  tsa_history: number[]
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

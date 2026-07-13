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
  baselines: {
    lag1: number
    roll3: number
    roll7: number
  }
  metrics: Record<string, number | null>
}

export type ForecastStatus = {
  run_id: string
  family: string
  anchor: string
  product: "forecast_operacional"
  holdout_mae: number | null
  holdout_r2: number | null
  interval_80_coverage: number | null
  artifact_path: string
}

export type ForecastRequest = {
  tsa_history: number[]
  carga_alcalina: number
  kappa: number
  db_sgf: number
  db_lab: number
  secura_pct: number
  casca_pct: number
  extrativo_total: number
  extrativo_at: number
  extrativo_sgf: number
  tpc: number
  idade: number
  vmi_le_021: number
  vmi_021_025: number
  vmi_gt_025: number
  pct_ab: number
  pct_c: number
  pct_dmg: number
}

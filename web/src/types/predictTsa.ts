export type PredictTsaRequest = {
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

export type PredictTsaResponse = {
  product: "what_if_direct"
  model_id: string
  family: string
  tsa_dia: number
  disclaimer: string
  metrics: {
    mae_holdout?: number | null
    r2_holdout?: number | null
  }
}

export type PredictTsaStatus = {
  run_id: string
  family: string
  product: "what_if_direct"
  holdout_mae: number | null
  holdout_r2: number | null
  artifact_path: string
  features: string[]
}

export type CurvePoint = {
  label: string
  tsa_dia: number
  carga_alcalina: number
  extrativo_at: number
}

export type Detractor = {
  feature: string
  delta_tsa: number
  method: "shap" | "coef" | "permutation"
}

export type InferenceResponse = {
  mode: "A" | "B"
  demo: boolean
  gate_ok: boolean
  model_id: string
  acceptance_run_id: string
  l2_dataset_version: string
  curves: CurvePoint[]
  detractors: Detractor[]
  warnings: string[]
  metrics: Record<string, number | null>
}

export type ValidateResponse = {
  ok: boolean
  row_count?: number | null
  sla_ms?: number | null
  signal?: string | null
  errors?: string[]
}

export type ReleaseStatus = {
  run_id: string
  release_ok: boolean
  demo_mode: boolean
  l2_dataset_version: string
  mae_tsa_holdout: number | null
  champions: Record<string, string>
  matriz_a_ok?: boolean | null
  matriz_b_ok?: boolean | null
  matriz_c_ok?: boolean | null
}

import type { ForecastFormValues } from "@/schemas/forecastSchema"

/** Valores de exemplo derivados de base/primeira_base.csv (primeiras linhas). */
export const FORECAST_EXAMPLE: ForecastFormValues = {
  tsa_history_text: "3289, 3250, 3250, 3250, 3400, 3450, 3470",
  carga_alcalina: 20.997,
  kappa: 17.523,
  prod_alcali_class: 1,
  db_sgf: 502.088,
  casca_pct: 0.832,
  extrativo_at: 2.68,
  tpc: 60.841,
  idade: 8.125,
  vmi_le_021: 0,
  vmi_021_025: 0,
  vmi_gt_025: 1,
  pct_ab: 0.167,
  pct_c: 0.352,
  pct_dmg: 0.481,
}

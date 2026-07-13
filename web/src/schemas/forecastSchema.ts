import { z } from "zod"

function parseTsaHistory(text: string): number[] {
  return text
    .split(/[,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => Number(s.replace(",", ".")))
}

export const forecastFormSchema = z.object({
  tsa_history_text: z
    .string()
    .min(1, "Informe o histórico de TSA")
    .refine((text) => parseTsaHistory(text).length >= 7, {
      message: "Informe ao menos 7 valores de TSA (ordem cronológica)",
    })
    .refine((text) => parseTsaHistory(text).every((n) => Number.isFinite(n)), {
      message: "Histórico contém valores inválidos",
    }),
  carga_alcalina: z.coerce.number(),
  kappa: z.coerce.number(),
  db_sgf: z.coerce.number(),
  db_lab: z.coerce.number(),
  secura_pct: z.coerce.number(),
  casca_pct: z.coerce.number(),
  extrativo_total: z.coerce.number(),
  extrativo_at: z.coerce.number(),
  extrativo_sgf: z.coerce.number(),
  tpc: z.coerce.number(),
  idade: z.coerce.number(),
  vmi_le_021: z.coerce.number(),
  vmi_021_025: z.coerce.number(),
  vmi_gt_025: z.coerce.number(),
  pct_ab: z.coerce.number(),
  pct_c: z.coerce.number(),
  pct_dmg: z.coerce.number(),
})

export type ForecastFormValues = z.infer<typeof forecastFormSchema>

export function toForecastRequest(values: ForecastFormValues) {
  return {
    tsa_history: parseTsaHistory(values.tsa_history_text),
    carga_alcalina: values.carga_alcalina,
    kappa: values.kappa,
    db_sgf: values.db_sgf,
    db_lab: values.db_lab,
    secura_pct: values.secura_pct,
    casca_pct: values.casca_pct,
    extrativo_total: values.extrativo_total,
    extrativo_at: values.extrativo_at,
    extrativo_sgf: values.extrativo_sgf,
    tpc: values.tpc,
    idade: values.idade,
    vmi_le_021: values.vmi_le_021,
    vmi_021_025: values.vmi_021_025,
    vmi_gt_025: values.vmi_gt_025,
    pct_ab: values.pct_ab,
    pct_c: values.pct_c,
    pct_dmg: values.pct_dmg,
  }
}

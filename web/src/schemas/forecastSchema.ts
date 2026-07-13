import { z } from "zod"

import { processVariablesSchema } from "@/schemas/processSchema"

function parseTsaHistory(text: string): number[] {
  return text
    .split(/[,;\s]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => Number(s.replace(",", ".")))
}

const tsaHistoryText = z
  .string()
  .min(1, "Informe o histórico de TSA")
  .refine((text) => parseTsaHistory(text).length >= 7, {
    message: "Informe ao menos 7 valores de TSA (ordem cronológica)",
  })
  .refine((text) => parseTsaHistory(text).every((n) => Number.isFinite(n)), {
    message: "Histórico contém valores inválidos",
  })

// Forecast operacional reutiliza as 13 variáveis de processo (mesmas faixas
// oficiais do backend) e adiciona o histórico TSA obrigatório.
export const forecastFormSchema = processVariablesSchema.extend({
  tsa_history_text: tsaHistoryText,
})

export type ForecastFormValues = z.infer<typeof forecastFormSchema>

export function toForecastRequest(values: ForecastFormValues) {
  return {
    tsa_history: parseTsaHistory(values.tsa_history_text),
    carga_alcalina: values.carga_alcalina,
    kappa: values.kappa,
    prod_alcali_class: values.prod_alcali_class,
    db_sgf: values.db_sgf,
    casca_pct: values.casca_pct,
    extrativo_at: values.extrativo_at,
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

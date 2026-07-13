import { z } from "zod"

export const processVariablesSchema = z.object({
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

export type ProcessVariablesValues = z.infer<typeof processVariablesSchema>

export const PROCESS_FIELDS: Array<{
  name: keyof ProcessVariablesValues
  label: string
  step?: string
}> = [
  { name: "carga_alcalina", label: "Carga alcalina" },
  { name: "kappa", label: "Kappa" },
  { name: "db_sgf", label: "DB SGF" },
  { name: "db_lab", label: "DB Lab" },
  { name: "secura_pct", label: "% Secura" },
  { name: "casca_pct", label: "% Casca" },
  { name: "extrativo_total", label: "Extrativo total" },
  { name: "extrativo_at", label: "Extrativo AT" },
  { name: "extrativo_sgf", label: "Extrativo SGF" },
  { name: "tpc", label: "TPC" },
  { name: "idade", label: "Idade" },
  { name: "vmi_le_021", label: "VMI ≤ 0,21", step: "1" },
  { name: "vmi_021_025", label: "VMI 0,21–0,25", step: "1" },
  { name: "vmi_gt_025", label: "VMI > 0,25", step: "1" },
  { name: "pct_ab", label: "A + B" },
  { name: "pct_c", label: "C" },
  { name: "pct_dmg", label: "D + MG" },
]

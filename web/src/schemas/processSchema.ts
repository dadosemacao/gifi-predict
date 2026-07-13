import { z } from "zod"

export const processVariablesSchema = z.object({
  carga_alcalina: z.coerce.number(),
  kappa: z.coerce.number(),
  prod_alcali_class: z.union([z.coerce.number(), z.enum(["baixo", "normal"])]),
  db_sgf: z.coerce.number(),
  casca_pct: z.coerce.number(),
  extrativo_at: z.coerce.number().optional(),
  tpc: z.coerce.number(),
  idade: z.coerce.number(),
  vmi_le_021: z.coerce.number().optional(),
  vmi_021_025: z.coerce.number().optional(),
  vmi_gt_025: z.coerce.number().optional(),
  pct_ab: z.coerce.number().optional(),
  pct_c: z.coerce.number().optional(),
  pct_dmg: z.coerce.number().optional(),
})

export type ProcessVariablesValues = z.infer<typeof processVariablesSchema>

export const PROCESS_FIELDS: Array<{
  name: keyof ProcessVariablesValues
  label: string
  step?: string
}> = [
  { name: "carga_alcalina", label: "Carga alcalina" },
  { name: "kappa", label: "Kappa" },
  { name: "prod_alcali_class", label: "Prod. álcali (0=baixo, 1=normal)" },
  { name: "db_sgf", label: "DB SGF" },
  { name: "casca_pct", label: "% Casca" },
  { name: "extrativo_at", label: "Extrativo AT" },
  { name: "tpc", label: "TPC" },
  { name: "idade", label: "Idade" },
  { name: "vmi_le_021", label: "VMI ≤ 0,21", step: "1" },
  { name: "vmi_021_025", label: "VMI 0,21–0,25", step: "1" },
  { name: "vmi_gt_025", label: "VMI > 0,25", step: "1" },
  { name: "pct_ab", label: "A + B" },
  { name: "pct_c", label: "C (aux. imputer)" },
  { name: "pct_dmg", label: "D + MG" },
]

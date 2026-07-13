import { z } from "zod"

// Faixas oficiais espelhadas de `src/serving/schemas.py` (ProcessVariablesInput)
// e `docs/kb/gifi-domain/specs/operational-ranges.yaml`. Falhar cedo no cliente
// evita 422 do backend e mantém a UI alinhada ao SSOT do domínio.

const cargaAlcalina = z.coerce
  .number()
  .min(17.5, "Carga alcalina fora da faixa oficial (17,5–21,0 % Na₂O)")
  .max(21.0, "Carga alcalina fora da faixa oficial (17,5–21,0 % Na₂O)")

const kappa = z.coerce
  .number()
  .min(15.0, "Kappa fora da faixa oficial (15,0–18,5)")
  .max(18.5, "Kappa fora da faixa oficial (15,0–18,5)")

const dbSgf = z.coerce
  .number()
  .min(465, "DB SGF fora da faixa oficial (465–515 kg/m³)")
  .max(515, "DB SGF fora da faixa oficial (465–515 kg/m³)")

const cascaPct = z.coerce
  .number()
  .max(1.5, "% Casca acima do limite oficial (máx. 1,5%)")

const tpc = z.coerce.number().min(45, "TPC abaixo de 45 dias (madeira verde)")

const prodAlcaliClass = z.union([z.coerce.number(), z.enum(["baixo", "normal"])])

// `extrativo_at` é opcional no contrato (imputado no serving quando ausente);
// demais auxiliares (vmi_*, pct_*) também são opcionais e derivados por tier.
const optionalNumber = z.coerce.number().optional()

export const processVariablesSchema = z.object({
  carga_alcalina: cargaAlcalina,
  kappa,
  prod_alcali_class: prodAlcaliClass,
  db_sgf: dbSgf,
  casca_pct: cascaPct,
  extrativo_at: optionalNumber,
  tpc,
  idade: z.coerce.number(),
  vmi_le_021: optionalNumber,
  vmi_021_025: optionalNumber,
  vmi_gt_025: optionalNumber,
  pct_ab: optionalNumber,
  pct_c: optionalNumber,
  pct_dmg: optionalNumber,
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

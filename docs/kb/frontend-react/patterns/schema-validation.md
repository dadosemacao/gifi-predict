# Schema Validation (Zod + RHF)

> **Purpose**: Validate scenario uploads and process forms at the UI boundary  
> **MCP Validated**: 2026-07-09 · **Atualizado**: 2026-07-13  
> **Sources**: Zod docs; align with Camada 1 template + `src/serving/schemas.py`

## When to Use

- Scenario Excel/CSV mapped to row objects
- Mode A/B column presence checks (mirror domain; backend still authoritative)
- Forecast / what-if process forms — espelhar faixas oficiais de `ProcessVariablesInput`

## Paridade de faixas (SSOT)

Espelhar `ProcessVariablesInput` (`src/serving/schemas.py`) e
`docs/kb/gifi-domain/specs/operational-ranges.yaml`. Falhar cedo no cliente
evita 422 e mantém a UI alinhada ao domínio. Backend permanece autoritativo.

| Campo | Faixa Zod (min/max) |
|-------|---------------------|
| `carga_alcalina` | 17,5 – 21,0 |
| `kappa` | 15,0 – 18,5 |
| `db_sgf` | 465 – 515 |
| `casca_pct` | ≤ 1,5 |
| `tpc` | ≥ 45 |
| `prod_alcali_class` | 0/1 ou `baixo`/`normal` |
| `extrativo_at`, `vmi_*`, `pct_*` | opcionais (imputados por tier no serving) |

SSOT único no front: `web/src/schemas/processSchema.ts`
(`processVariablesSchema` + `PROCESS_FIELDS`); `forecastFormSchema` faz
`.extend()` para adicionar `tsa_history_text`.

## Implementation

```ts
import { z } from "zod"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"

const mixSchema = z.object({
  pct_A: z.number(), pct_B: z.number(), pct_C: z.number(),
  pct_D: z.number(), pct_MG: z.number(),
}).superRefine((m, ctx) => {
  const s = m.pct_A + m.pct_B + m.pct_C + m.pct_D + m.pct_MG
  if (Math.abs(s - 1) > 0.02) {
    ctx.addIssue({ code: "custom", message: "mix_sum_tol" })
  }
})

export const scenarioSchema = z.object({
  mode: z.enum(["A", "B"]),
  cenario_id: z.string().min(1),
  idade: z.number().nonnegative(),
  tpc_dias: z.number(),
  volume_m3: z.number().positive(),
  db_sgf: z.number(),
  kappa: z.number(),
  mix: mixSchema,
  extrativo_at: z.number().optional(),
  carga_alcalina: z.number().optional(),
}).superRefine((v, ctx) => {
  if (v.mode === "A" && (v.extrativo_at != null || v.carga_alcalina != null)) {
    ctx.addIssue({ code: "custom", message: "mode_a_forbids_inject" })
  }
})

export type ScenarioForm = z.infer<typeof scenarioSchema>

export function useScenarioForm() {
  return useForm<ScenarioForm>({ resolver: zodResolver(scenarioSchema) })
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| template version | `v0` | Bump with Camada 1 |
| server | always re-validate | UI is UX only |

## Example Usage

`safeParse` on parsed spreadsheet rows before POST.

## See Also

- gifi-domain `scenario-column-contract`
- [service-layer.md](service-layer.md)

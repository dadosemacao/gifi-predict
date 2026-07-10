# Schema Validation (Zod + RHF)

> **Purpose**: Validate scenario uploads at the UI boundary  
> **MCP Validated**: 2026-07-09  
> **Sources**: Zod docs; align with Camada 1 template

## When to Use

- Scenario Excel/CSV mapped to row objects
- Mode A/B column presence checks (mirror domain; backend still authoritative)

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

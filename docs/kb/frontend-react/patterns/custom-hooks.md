# Custom Hooks

> **Purpose**: Reuse orchestration without duplicating Query/RHF glue  
> **MCP Validated**: 2026-07-09

## When to Use

- Upload + invalidate inference
- Shared mode/URL sync
- Browser-only subscriptions (then Effects are OK)

## Implementation

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { uploadScenario } from "@/services/scenarioApi"

export function useScenarioSubmit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: uploadScenario,
    onSuccess: async (job) => {
      await qc.invalidateQueries({ queryKey: ["inference", job.id] })
    },
  })
}
```

Hooks return state + actions. They must not embed JSX. Domain rejects stay typed from API errors.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| location | `features/*/use*.ts` or `hooks/` | Prefer feature-local |
| naming | `useVerbNoun` | — |

## Example Usage

Form `onSubmit={mutate}` — no Effect watching form values.

## See Also

- [../concepts/effect-discipline.md](../concepts/effect-discipline.md)
- [service-layer.md](service-layer.md)

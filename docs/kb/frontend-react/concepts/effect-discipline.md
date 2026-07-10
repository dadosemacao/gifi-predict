# Effect Discipline

> **Purpose**: Avoid useEffect for business orchestration  
> **Confidence**: 0.90  
> **MCP Validated**: 2026-07-09  
> **Source**: React “You Might Not Need an Effect”

## Overview

Effects synchronize with external systems (subscriptions, DOM).  
Do **not** use Effects to fire scenario inference because a form field changed, or to chain “upload then predict then plot” as cascading Effects.

## The Concept

| Use Effect | Prefer event / Query |
|------------|----------------------|
| window listener | — |
| Imperative chart resize observer | — |
| Upload on submit | `onSubmit` → `mutation.mutate` |
| Refetch after save | `onSuccess` invalidateQueries |
| Derive view model | Compute during render |

```tsx
// Wrong — orchestration via Effect
useEffect(() => {
  if (file) runInference(file)
}, [file])

// Correct — user action
async function onSubmit(values: ScenarioForm) {
  const job = await uploadMutation.mutateAsync(values)
  await queryClient.invalidateQueries({ queryKey: ["inference", job.id] })
}
```

## Quick Reference

| Smell | Refactor |
|-------|----------|
| Effect depends on form fields to call API | Submit handler |
| Effect copies props → state | Render derived value |
| Effect chains A→B→C | async function / mutation |

## Common Mistakes

### Wrong

Three Effects: parse file → post → set chart state.

### Correct

One mutation pipeline in a custom hook returning `{ submit, status, data }`.

## Related

- [state-separation.md](state-separation.md)
- [../patterns/custom-hooks.md](../patterns/custom-hooks.md)

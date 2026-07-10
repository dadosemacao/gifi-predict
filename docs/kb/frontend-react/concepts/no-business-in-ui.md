# No Business Rules in Presentational Components

> **Purpose**: Keep Camada 1/4 rules out of dumb UI  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio

## Overview

Presentational components render props. They do **not** decide Modo A forbids inject, MAE≤56, or DB faixas.  
Those live in domain services, Zod schemas derived from Camada 1, and backend validation.

## The Concept

| Allowed in presentational | Forbidden |
|---------------------------|-----------|
| Format numbers / dates | Compute MAE gates |
| Disable button from `disabled` prop | Infer Elo routing |
| Map `detratores[]` to list | Invent ΔTSA formulas |
| i18n labels | Change template ownership |

```tsx
// Presentational — OK
export function DetractorsList({ items }: { items: { name: string; deltaTsa: number }[] }) {
  return (
    <ul>
      {items.map((d) => (
        <li key={d.name}>{d.name}: {d.deltaTsa.toFixed(1)}</li>
      ))}
    </ul>
  )
}
```

Containers call services/hooks; schemas enforce column contract; API rejects Modo A inject.

## Quick Reference

| Layer | Owns rules? |
|-------|-------------|
| Presentational | No |
| Container / hook | Orchestration only |
| schemas/ + services/ | Boundary validation |
| Backend + Camada 1/4 | Normative SSOT |

## Common Mistakes

### Wrong

`if (tpc < 45) showGreenPenalty` hard-coded in chart.

### Correct

Backend flags / Matrix C payload drives the panel.

## Related

- [../patterns/container-presentational.md](../patterns/container-presentational.md)
- gifi-domain scenario contracts

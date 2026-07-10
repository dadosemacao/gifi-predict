# State Separation

> **Purpose**: Local vs global vs remote vs URL — don't conflate  
> **Confidence**: 0.90  
> **MCP Validated**: 2026-07-09  
> **Sources**: TanStack Query v5; React docs

## Overview

Server state is a cache of remote facts. UI chrome is local/global.  
GIFI inference results belong in TanStack Query, not Zustand by default.

## The Concept

| Kind | Owner | Examples |
|------|-------|----------|
| Local | Component / RHF | draft cells, wizard step |
| Global UI | Zustand (optional) | theme, nav collapsed |
| Remote | QueryClient | upload job, TSA series, top-3 |
| URL | Router | `?mode=A&cenario=...` |

```tsx
// Remote — Query
const { data } = useQuery({ queryKey: ["inference", id], queryFn: () => api.get(id) })

// Local — form
const form = useForm<ScenarioForm>({ resolver: zodResolver(schema) })

// URL — shareable mode
const [params] = useSearchParams()
const mode = params.get("mode") === "B" ? "B" : "A"
```

**Zustand justification**: only when many distant components need the *same* ephemeral UI flag and props/context become noise. Never for MAE tables.

## Quick Reference

| Symptom | Fix |
|---------|-----|
| Duplicate fetches | Query keys |
| Lost share link | Put filters in URL |
| Store holds API JSON | Move to Query |

## Common Mistakes

### Wrong

`useEffect` syncing Query data into Zustand “source of truth”.

### Correct

Read Query in containers; pass props to presentational views.

## Related

- [effect-discipline.md](effect-discipline.md)
- [../patterns/state-separation.md](../patterns/state-separation.md)

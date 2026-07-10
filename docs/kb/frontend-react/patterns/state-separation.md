# State Separation Playbook

> **Purpose**: Concrete placement rules for GIFI UI state  
> **MCP Validated**: 2026-07-09

## When to Use

- Designing a new feature
- Reviewing PRs that introduce Zustand or Context

## Implementation

```text
Decision tree
├── Is it from the server / inference API? → TanStack Query
├── Must it be shareable via link? → URL search params
├── Needed by one form/wizard? → RHF / local useState
├── Ephemeral UI chrome across distant trees? → Zustand (justify in PR)
└── Domain rule / gate? → NOT in frontend state — backend/Camada 4
```

```tsx
// Anti-pattern
const useTsaStore = create((set) => ({ series: [], setSeries: (s) => set({ series: s }) }))
useEffect(() => {
  api.get(id).then((d) => useTsaStore.getState().setSeries(d.series))
}, [id])

// Pattern
const { data } = useQuery({ queryKey: ["inference", id], queryFn: () => getInference(id) })
```

## Configuration

| State kind | Default tool | GIFI example |
|------------|--------------|--------------|
| remote | Query | TSA curve |
| URL | router | mode=A\|B |
| local | RHF | upload sheet |
| global UI | Zustand opt. | densitiy units toggle display |

## Example Usage

PR checklist: “Where does this state live?” comment required for new stores.

## See Also

- [../concepts/state-separation.md](../concepts/state-separation.md)
- [provider-pattern.md](provider-pattern.md)

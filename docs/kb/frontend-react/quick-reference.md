# Frontend React Quick Reference

> GIFI Camada 5 UI. **MCP Validated:** 2026-07-09 · Emerson Antônio

## Stack (MVP)

| Layer | Choice |
|-------|--------|
| App | React + TypeScript + Vite |
| Style | Tailwind + Shadcn (`components/ui`) |
| Forms | React Hook Form + Zod |
| Server state | TanStack Query v5 |
| Client global | Zustand **only if justified** |
| Tests | Vitest + Testing Library |

## Folder structure

```text
src/
  app/                 # providers, router shell
  features/            # scenario-upload, curves, detractors, ...
  components/
    ui/                # shadcn primitives
    layout/
    shared/
  hooks/
  services/            # HTTP / inference clients
  lib/
  schemas/             # Zod (mirror template contract)
  types/
  stores/              # rare; prefer Query + local
  routes/
```

## State separation

| Kind | Tool | Example |
|------|------|---------|
| Local | useState / RHF | form drafts |
| Global UI | Zustand (sparse) | sidebar open |
| Remote | TanStack Query | inference result |
| URL | router search | cenario_id, mode |

## Design patterns checklist

| Pattern | Rule |
|---------|------|
| Feature Folder | Colocate by feature |
| Container/Presentational | No fetch/rules in dumb UI |
| Custom Hooks | Reuse logic, not JSX soup |
| Service Layer | API behind services/* |
| Schema Validation | Zod at boundary |
| Provider | QueryClient once |
| Error Boundary | Wrap feature trees |
| State Separation | Don't dump remote into Zustand |
| Production Curves | Recharts LineChart; presentational only |

## Curves DTO

| Field | Series |
|-------|--------|
| `tsa_dia` | TSA/dia |
| `carga_alcalina` | Carga (Elo 2) |
| `extrativo_at` | Extrativos (Elo 1) |

## Pitfalls

| Don't | Do |
|-------|-----|
| Put MAE/faixas logic in components | Call services; domain in backend/KB |
| useEffect to “run simulation” | Event handler → mutation |
| Recreate QueryClient each render | useState(() => new QueryClient()) |
| Own template schema in UI | Import/version from Camada 1 |
| Ship as prod without gate | Bind demo flag until A∧B∧C |

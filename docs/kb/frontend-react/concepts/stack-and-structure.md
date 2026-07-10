# Stack and Structure

> **Purpose**: Canonical Vite React app layout for GIFI Camada 5  
> **Confidence**: 0.90  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio

## Overview

Prefer **Vite** for local MVP speed. Tailwind+Shadcn for UI primitives.  
Business acceptance stays in Camada 4; UI consumes released artifacts.

## The Concept

```text
src/
  app/           # App.tsx, providers.tsx, router
  features/      # scenario-upload/, production-curves/, detractors-panel/
  components/
    ui/          # button, card, table (shadcn)
    layout/      # shell, header
    shared/      # cross-feature presentational
  hooks/         # useScenarioUpload, useInferenceJob
  services/      # scenarioApi, inferenceApi
  lib/           # cn(), formatters (display only)
  schemas/       # zod scenarios — aligned to template_cenario_vN
  types/
  stores/        # optional thin UI stores
  routes/
```

| Concern | Location |
|---------|----------|
| Template version | `schemas/` from Camada 1 contract |
| Upload IO | `services/` |
| Form UX | `features/scenario-upload` |
| Curves chart | presentational + container |

## Quick Reference

| Prefer | Avoid |
|--------|-------|
| Vite SPA MVP | Heavy Next.js unless SSR required |
| Feature folders | Huge `pages/` dump |
| Query for remote | Zustand for server payloads |

## Common Mistakes

### Wrong

Encoding faixas TSA/DB inside chart components.

### Correct

Display-only formatting; thresholds from API/config published by domain.

## Related

- [state-separation.md](state-separation.md)
- [../patterns/feature-folder.md](../patterns/feature-folder.md)

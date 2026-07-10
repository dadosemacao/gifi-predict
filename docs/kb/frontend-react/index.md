# Frontend React Knowledge Base (GIFI Camada 5)

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.1

> **Purpose**: React+TS UI patterns for GIFI scenario surface — no domain rules in presentational components  
> **Confidence**: 0.90 (React/TanStack/Zod MCP + GIFI Camada 5 requirements)  
> **MCP Validated**: 2026-07-09  
> **Stack**: React+TS, Vite, Tailwind+Shadcn, RHF+Zod, TanStack Query, Vitest+RTL; Zustand only if justified

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/stack-and-structure.md](concepts/stack-and-structure.md) | Folder layout + stack choices |
| [concepts/state-separation.md](concepts/state-separation.md) | Local / global / remote / URL |
| [concepts/no-business-in-ui.md](concepts/no-business-in-ui.md) | Domain rules stay off presentational layer |
| [concepts/effect-discipline.md](concepts/effect-discipline.md) | Avoid useEffect for business orchestration |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/feature-folder.md](patterns/feature-folder.md) | Feature Folder organization |
| [patterns/container-presentational.md](patterns/container-presentational.md) | Container / Presentational |
| [patterns/custom-hooks.md](patterns/custom-hooks.md) | Custom Hooks |
| [patterns/service-layer.md](patterns/service-layer.md) | Service Layer |
| [patterns/schema-validation.md](patterns/schema-validation.md) | Schema Validation (Zod+RHF) |
| [patterns/provider-pattern.md](patterns/provider-pattern.md) | Provider Pattern |
| [patterns/error-boundary.md](patterns/error-boundary.md) | Error Boundary |
| [patterns/state-separation.md](patterns/state-separation.md) | State Separation playbook |
| [patterns/production-curves-chart.md](patterns/production-curves-chart.md) | Recharts TSA / Carga / Extrativos |

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Camada 5** | Upload template → curves → top-3; consumes Camada 3/4 |
| **Template ownership** | Camada 1 owns schema; UI only instantiates |
| **Demo vs release** | UI can demo; prod needs A∧B∧C gate |

## Agent Usage

| Agent | Use Case |
|-------|----------|
| `react-frontend-architect` | Structure, patterns, stack |
| `gifi-domain-specialist` | Scenario column rules |
| `gifi-acceptance-engineer` | Whether UI may bind prod model |

## Quick Reference

- [quick-reference.md](quick-reference.md)

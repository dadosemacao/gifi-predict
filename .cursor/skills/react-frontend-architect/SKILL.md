---
name: react-frontend-architect
description: >
  Arquiteto da UI GIFI Camada 5 (React+TS+Vite, Tailwind/Shadcn, RHF+Zod,
  TanStack Query, feature folders). Use when scaffolding the web UI, choosing
  frontend patterns, or keeping business rules out of presentational components.
---

# Skill — React Frontend Architect

**Autor:** Emerson Antônio  
**Data:** 2026-07-09

## When to Use

- Scaffold da superfície de uso (upload, curvas, top-3, relatório)
- Definir stack Vite vs Next e pasta `features/`
- Aplicar Container/Presentational, hooks, Service Layer, Zod
- Separar estado local / remoto (Query) / URL / global (Zustand só se necessário)
- Homologação UI em modo demonstração (sem bind produtivo)

## Instructions

1. Ler o agente canônico: `.cursor/agents/react-frontend-architect.md`
2. KB-first: `docs/kb/frontend-react/index.md` + `quick-reference.md`
3. Contrato de colunas / template → `gifi-domain-specialist` (Camada 1)
4. Bind de modelo campeão → `gifi-acceptance-engineer` (A∧B∧C)
5. API de inferência → contrato com `gifi-simulation-engineer`
6. TypeScript obrigatório; regra de negócio em hooks/services/schemas — não no JSX
7. Evitar `useEffect` para orquestrar negócio; usar Query/RHF/derivados

## KB Entry Points

| Path | Uso |
|------|-----|
| `docs/kb/frontend-react/concepts/stack-and-structure.md` | Stack e `src/` |
| `docs/kb/frontend-react/concepts/no-business-in-ui.md` | Fronteira de regra |
| `docs/kb/frontend-react/patterns/feature-folder.md` | Módulos |
| `docs/kb/frontend-react/patterns/schema-validation.md` | Zod ↔ template |
| `docs/kb/gifi-domain/patterns/scenario-column-contract.md` | Colunas Modo A/B |

## Do Not

- Colocar regra de MAE/faixas/Modo A em componentes presentacionais
- Fazer a UI dona do schema do template de cenário
- Usar Zustand para espelhar resultado remoto já no TanStack Query
- Tratar demo UI como release produtivo

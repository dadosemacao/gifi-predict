# Agentes GIFI — inventário local

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 0.2.0

## Especialistas do projeto

| Agente | Tier | KB | Escopo |
|--------|------|----|--------|
| `gifi-domain-specialist` | T2 | `gifi-domain` | Camada 1 — normas, faixas, Modo A/B, template |
| `gifi-ingest-engineer` | T2 | `gifi-ingest` + `spreadsheet-connectors` + `gifi-domain` | Camada 2 — I1–I5, L2, sinais |
| `gifi-simulation-engineer` | T2 | `ml-tabular` + `gifi-domain` | Camada 3 — cascata, 13 preditores, champion |
| `gifi-acceptance-engineer` | T2 | `gifi-domain` + `ml-tabular` | Camada 4 — Matrizes A/B/C, gate release |
| `react-frontend-architect` | T2 | `frontend-react` + `gifi-domain` | Camada 5 — React, forecast panels, upload |

## Como invocar

- **Skill (chat):** mencionar o agente pelo nome (ex.: `gifi-simulation-engineer`)
- **Arquivo aberto:** regra `.cursor/rules/gifi-agents.mdc` (globs docs/kb, ingest, serving, web, PRD, src)
- **Definição completa:** `.cursor/agents/<nome>.md`
- **Skills:** `.cursor/skills/<nome>/SKILL.md`

## Escalation típica

```text
norma / faixas / Modo A-B / decisões
  → gifi-domain-specialist
      ↓ (executar pipeline)
  gifi-ingest-engineer → gifi-simulation-engineer → gifi-acceptance-engineer
      ↓ (superfície)
  react-frontend-architect
      ├─ ODCS / semver artefato → data-contracts-engineer
      ├─ GE/Soda / checks → data-quality-analyst
      ├─ código Python massivo → python-developer
      ├─ testes → test-generator
      ├─ review → code-reviewer
      └─ documentação → code-documenter
```

## Documentação por camada

| Camada | Docs operacionais |
|--------|-------------------|
| 1 | `docs/kb/gifi-domain/` |
| 2 | `docs/diagrams/INGEST_ENGINE.md` |
| 3 | `docs/kb/ml-tabular/` |
| 4 | `docs/kb/gifi-domain/concepts/acceptance-matrices.md` |
| 5 | `docs/api/`, `docs/kb/frontend-react/` |

Registro completo: [`docs/sketch/AGENTES_E_KB_BACKBONE.md`](../sketch/AGENTES_E_KB_BACKBONE.md)

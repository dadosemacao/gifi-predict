# Agentes GIFI — inventário local

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.1.1

## Especialistas do projeto

| Agente | Tier | KB | Escopo |
|--------|------|----|--------|
| `gifi-domain-specialist` | T2 | `gifi-domain` | Camada 1 — normas |
| `gifi-ingest-engineer` | T2 | `gifi-ingest` + `spreadsheet-connectors` + `gifi-domain` | Camada 2 — I1–I5 |

## Como invocar

- **Skill (chat):** mencionar `gifi-domain-specialist` ou `gifi-ingest-engineer`
- **Arquivo aberto:** regra `.cursor/rules/gifi-agents.mdc` (globs docs/kb, ingest, PRD, src)
- **Definição completa:** `.cursor/agents/<nome>.md`

## Escalation típica

```text
norma / faixas / Modo A-B / decisões
  → gifi-domain-specialist
      ↓ (executar pipeline)
  gifi-ingest-engineer
      ├─ ODCS / semver artefato → data-contracts-engineer
      ├─ GE/Soda / checks → data-quality-analyst
      ├─ código Python massivo → python-developer
      ├─ testes → test-generator
      └─ DAG → pipeline-architect / airflow-specialist
```

---
name: gifi-domain-specialist
description: >
  Guardião normativo da Camada 1 do GIFI (regras do brief, faixas, Modo A/B,
  decisões fechadas, template de cenário). Use when validating domain rules,
  mix/DB/TSA thresholds, Mode A/B, holdout, Elo 1b scope, or scenario templates.
---

# Skill — GIFI Domain Specialist

**Autor:** Emerson Antônio  
**Data:** 2026-07-09

## When to Use

- Validar regras TSA&lt;1000, kg/m³, k=0,985, mix±0,02, DB[350,650]
- Classificar zonas ótima/aceitável/crítica
- Decidir Modo A vs B / colunas do template de cenário
- Aplicar decisões D-A..D-G (holdout, Elo 1b NO-GO, etc.)
- Checar se features Mix A/B/C estão completas no contrato

## Instructions

1. Ler o agente canônico: `.cursor/agents/gifi-domain-specialist.md`
2. Seguir KB-first: `docs/kb/gifi-domain/index.md` + `quick-reference.md`
3. Números apenas de `docs/kb/gifi-domain/specs/*.yaml` ou DECISOES/PRD citados
4. Não implementar I1–I5 — escalar para skill/agente `gifi-ingest-engineer`
5. Responder no formato de parecer do agente (Status + Confidence + Sources)

## KB Entry Points

| Path | Uso |
|------|-----|
| `docs/kb/gifi-domain/quick-reference.md` | Lookup rápido |
| `docs/kb/gifi-domain/specs/domain-rules.yaml` | Regras numéricas |
| `docs/kb/gifi-domain/specs/operational-ranges.yaml` | Faixas |
| `docs/sketch/DECISOES_GIFI.md` | Decisões Confirmadas |

## Do Not

- Inventar limiares
- Usar fator 0,88 ou g/cm³
- Estimar % Casca no MVP (D-B)
- Alterar decisão Confirmada sem change request

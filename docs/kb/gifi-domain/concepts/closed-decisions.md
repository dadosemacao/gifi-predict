# Closed Decisions

> **Purpose**: Decisões que destravam o build; change request se alteradas  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: `docs/sketch/DECISOES_GIFI.md`

## Overview

Status: Confirmada (stakeholder) ou Assumida (CD). Confirmadas não mudam sem solicitação formal.

## The Concept

| ID | Decisão | Status |
|----|---------|--------|
| D-A | Holdout 2025-05-01..2025-10-30; treino ≤ 2025-04-30 | Confirmada |
| D-B | Elo 1b (% Casca) = NO-GO no MVP | Confirmada |
| D-C | Agregação turno→dia: média ponderada (qualidade); soma (volume); TSA meta diária | Assumida CD |
| D-D | Artefatos: Parquet + manifesto JSON | Assumida CD |
| D-E | `template_cenario_v0` na Camada 1 | Assumida CD |
| D-F | Base interpolada TI — fallback Excel | Encaminhada |
| D-G | SLA reprocesso TI (proposta ≤ 2 DU) | Encaminhada |

## Quick Reference

| Impacto Ingest | Regra |
|----------------|-------|
| I4 holdout | Partição D-A |
| I3 Casca | Só feature se medida |
| I4 formato | Parquet + JSON |
| I1 cenário | Template D-E antes da UI |

## Common Mistakes

### Wrong

Treinar com dados de mai–out/2025 e avaliar no mesmo período.

### Correct

Holdout exclusivo nas datas D-A; treino corta em 2025-04-30.

## Related

- [target-and-framing.md](target-and-framing.md)
- `docs/sketch/DECISOES_GIFI.md`

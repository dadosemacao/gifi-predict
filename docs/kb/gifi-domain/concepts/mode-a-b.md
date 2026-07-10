# Mode A vs Mode B

> **Purpose**: Separar simulação integrada de isolamento de elos  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: PRD §4.1; ingest-engine §1.1 / I2

## Overview

Upload de cenário (Camada 5) entrega instância; Camada 1 define o contrato do template. Modo A não aceita Extrativo/Carga injetados; Modo B permite.

## The Concept

| Modo | Uso | Entradas usuário | Extrativo / Carga |
|------|-----|------------------|-------------------|
| **A Integração** | Longo prazo / e2e | Sítio, Idade, Mix, TPC, Volume, DB_SGF, Kappa | Estimados (cascata) |
| **B Isolamento** | Estresse / diagnóstico | + injeção opcional | Medidos permitidos |

Cascata (referência):

```text
Elo 1:  Sítio + Idade (+ mix) → Extrativo_AT
Elo 1b: NO-GO MVP (Casca não estimada)
Elo 2:  Extrativo + TPC + DB_SGF → Carga
Elo 3:  Mix + qualidade + processo → TSA/dia
```

## Quick Reference

| Validação upload | Modo A | Modo B |
|------------------|--------|--------|
| Extrativo injetado | rejeitar | aceitar |
| Carga injetada | rejeitar | aceitar |
| DB_LAB medido | opcional | permitido |
| Sinal rejeição | `INGEST_SCENARIO_REJECT` | idem se fora template |

## Common Mistakes

### Wrong

Permitir injeção no Modo A “só para teste rápido” na UI.

### Correct

Trocar para Modo B ou remover colunas injetadas.

## Related

- [../patterns/scenario-template-contract.md](../patterns/scenario-template-contract.md)
- [closed-decisions.md](closed-decisions.md)

# Signal Catalog

> **Purpose**: Catálogo macro de sinais entre Ingest e Backbone  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §4.3

## Overview

Sinais são o único idioma operacional entre Ingest e Confiança/Motor/UI. Severidade define se publica ou isola.

## The Concept

| Código | Severidade | Significado | Efeito |
|--------|------------|-------------|--------|
| `INGEST_SCHEMA_FAIL` | Bloqueante | Coluna/tipo/unidade inválidos | Sem update Motor/Confiança |
| `INGEST_MIX_FAIL` | Bloqueante | Soma pct fora ±0,02 | Idem |
| `INGEST_UNIT_FAIL` | Bloqueante | Densidade fora escala kg/m³ | Idem |
| `INGEST_SOURCE_MISSING` | Bloqueante | Fonte ausente/ilegível | Sem publicação |
| `INGEST_SCENARIO_REJECT` | Bloqueante | Upload fora template A/B | UI erro; sem inferência |
| `ACCEPT_DATA_REJECT` | Bloqueante* | Confiança devolve lote | Remediação + reprocesso |
| `INGEST_PROXY_DB` | Aviso | DB_LAB imputado 0,985×SGF | Publica com flag |
| `INGEST_SPARSE_LAB` | Aviso | Extrativo/Casca esparsos | Alertar Elo1 / Matriz A |
| `INGEST_FILTER_INFO` | Info | Removidos TSA < 1000 | Segue; conta manifesto |

\*Gerado na Camada 4, consumido pelo Ingest.

Tipos agregados: `ingest_ok` | `ingest_warn` | `ingest_fail`.

## Quick Reference

| Tipo | Ação |
|------|------|
| Bloqueante | Quarentena; last-good permanece |
| Aviso | Publica se matriz admitir |
| Info | Segue |

## Common Mistakes

### Wrong

Inventar warning novo e publicar como “ok com ressalva”.

### Correct

Warning novo = bloqueante até entrar na matriz (default).

## Related

- [../specs/signal-catalog.yaml](../specs/signal-catalog.yaml)
- [../patterns/warning-admissibility.md](../patterns/warning-admissibility.md)

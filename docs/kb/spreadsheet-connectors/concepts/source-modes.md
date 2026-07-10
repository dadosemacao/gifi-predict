# Source Modes

> **Purpose**: Classificar origem e modo operacional do I1  
> **Confidence**: 0.90  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §2 I1; PRD §3.1

## Overview

Todo conector termina classificando o lote como Histórico (treino/holdout) ou Cenário (inferência Modo A/B). Fontes históricas preferem TI; Excel é fallback.

## The Concept

| Mode | Natureza | Fontes típicas |
|------|----------|----------------|
| `historical` | Batch | Excel consolidado; tabelas TI limpas/interpoladas |
| `scenario` | Online | Instância de `template_cenario_vN` via UI |

```text
if source is TI tables available:
    prefer TI (D-F acelera)
else:
    Excel QM×Processo consolidado

scenario never uses TI historical tables
```

## Quick Reference

| Check | Histórico | Cenário |
|-------|-----------|---------|
| Hash lote | Sim | Sim (arquivo) |
| Quarentena | Sim | Não |
| Template L1 | N/A schema fonte | Obrigatório |

## Common Mistakes

### Wrong

Tratar upload de cenário com o mesmo pipeline batch/quarentena.

### Correct

Classificar `mode` cedo e ramificar dual-path.

## Related

- [batch-identity.md](batch-identity.md)
- `docs/kb/gifi-ingest/patterns/dual-path-execution.md`

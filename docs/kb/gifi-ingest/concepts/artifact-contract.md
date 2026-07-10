# Artifact Contract

> **Purpose**: Contrato mínimo de todo artefato publicado pelo Ingest  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §4.2

## Overview

Nomes semânticos (`train_features` etc.) não bastam. Motor recusa `schema_version` major diferente do esperado.

## The Concept

| Elemento | Regra |
|----------|-------|
| PK histórico | `data_processo` + `turno` |
| PK cenário | `cenario_id` + `linha` |
| Timestamp ref. | `data_processo` (não ingest_at) |
| Schema | `schema_version` semver |
| Dados | `dataset_version` + `source_hash` |
| Compat | minor = BC; major = breaking + aceite L4 |
| Colunas | lista fixa; coluna nova sem major = proibida |
| Flags | `db_origin ∈ {lab,proxy}`; `extr_origin ∈ {medido,estimado}` |
| Formato | Parquet datasets; JSON manifesto |

Artefatos: `train_features`, `holdout_features`, `infer_features`, manifesto, relatório de qualidade, sinais.

## Quick Reference

| Destino | Entrega |
|---------|---------|
| Camada 3 | train / infer + manifesto |
| Camada 4 | holdout + qualidade + sinais |
| Camada 5 | aceito/rejeitado upload |
| Camada 2 estado | última versão boa |

## Common Mistakes

### Wrong

Ordenar holdout por `ingested_at`.

### Correct

Ordenar e particionar por `data_processo`.

## Related

- [../specs/artifact-contract.yaml](../specs/artifact-contract.yaml)
- `docs/kb/gifi-domain/concepts/closed-decisions.md`

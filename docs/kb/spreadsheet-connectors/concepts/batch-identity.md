# Batch Identity

> **Purpose**: Identificar lote de forma auditável (nome, hash, período)  
> **Confidence**: 0.90  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §2 I1; §4.2 source_hash

## Overview

Sem identidade estável não há remediação rastreável nem `dataset_version`/`source_hash` no manifesto. Hash deve cobrir conteúdo, não apenas path.

## The Concept

```yaml
batch_identity:
  batch_name: string          # humano
  source_hash: sha256         # bytes ou export canônico
  mode: historical | scenario
  period_start: date | null   # histórico
  period_end: date | null
  ingested_at: datetime_utc
  source_kind: excel | ti_table | scenario_upload
  source_uri: string
```

Reprocesso = novo lote com novo hash/versão, mesmo se o nome humano repetir.

## Quick Reference

| Evento | Ação em identidade |
|--------|--------------------|
| Mesmo arquivo republicado idêntico | Mesmo hash → possível skip idempotente |
| Arquivo corrigido | Novo hash → novo lote |
| Remediação | Registrar hash_antes / hash_depois |

## Common Mistakes

### Wrong

```python
source_hash = hashlib.sha256(path.encode()).hexdigest()
```

### Correct

```python
source_hash = sha256_file_bytes(path)
```

## Related

- [../specs/batch-manifest-source.yaml](../specs/batch-manifest-source.yaml)
- `docs/kb/gifi-ingest/concepts/artifact-contract.md`

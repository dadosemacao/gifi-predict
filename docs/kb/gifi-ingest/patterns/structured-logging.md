# Structured Logging (I5)

> **Purpose**: Contrato mínimo de logs do Ingest Engine para auditoria e remediação  
> **Validated**: 2026-07-10  
> **Autor**: Emerson Antônio  
> **Fonte**: ingest-engine §2 I5; specs/remediation-evidence.yaml

## When to Use

- Implementar I5 (batch e online)
- Correlacionar lote, sinais e duração no ciclo de remediação
- Integrar com observabilidade futura (cloud) sem bloquear MVP local

## Implementation

Todo evento de ingestão emite **uma linha JSON** por marco (início, fim, sinal, quarentena).

### Campos obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | ISO8601 | Momento do evento |
| `level` | enum | `INFO`, `WARN`, `ERROR` |
| `event` | string | `ingest_start`, `ingest_end`, `signal_emitted`, `quarantine` |
| `path` | enum | `historical_batch` \| `scenario_online` |
| `batch_id` | string | UUID do lote ou upload |
| `source_hash` | string | Hash da fonte (batch); vazio no online se N/A |
| `component` | enum | `I1`..`I5` |

### Campos por evento `ingest_end`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `duration_ms` | int | Duração total |
| `rows_read` | int | Linhas lidas na fonte |
| `rows_written` | int | Linhas no artefato |
| `rows_excluded` | int | Ex.: TSA < 1.000 |
| `publish_status` | enum | `published_ok`, `published_with_warnings`, `quarantined`, `failed` |
| `signals` | string[] | Códigos emitidos (ex.: `INGEST_PROXY_DB`) |
| `schema_version` | string | Semver do artefato |

### Campos path `scenario_online`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `cenario_id` | string | ID do upload |
| `row_count` | int | Linhas validadas |
| `sla_ms` | int | Tempo de validação |
| `template_id` | string | `template_cenario_v0` |
| `reject_reason` | string | Se `INGEST_SCENARIO_REJECT` |

### Exemplo (batch)

```json
{
  "timestamp": "2026-07-10T15:00:00-03:00",
  "level": "INFO",
  "event": "ingest_end",
  "path": "historical_batch",
  "batch_id": "b7c9e2a1-...",
  "source_hash": "sha256:abc...",
  "component": "I4",
  "duration_ms": 45230,
  "rows_read": 125000,
  "rows_written": 118400,
  "rows_excluded": 3200,
  "publish_status": "published_with_warnings",
  "signals": ["INGEST_PROXY_DB", "INGEST_FILTER_INFO"],
  "schema_version": "1.0.0"
}
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `sink` | stdout | MVP local; arquivo ou cloud depois |
| `correlation_id` | = `batch_id` | Rastreio ponta a ponta |

## See Also

- [remediation-cycle.md](remediation-cycle.md)
- [../specs/remediation-evidence.yaml](../specs/remediation-evidence.yaml)
- [../specs/signal-catalog.yaml](../specs/signal-catalog.yaml)

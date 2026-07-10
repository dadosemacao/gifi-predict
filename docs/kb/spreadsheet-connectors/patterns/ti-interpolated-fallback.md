# TI Interpolated Fallback

> **Purpose**: Preferir tabelas TI; não bloquear build se ausentes  
> **Validated**: 2026-07-09  
> **Fonte**: DECISOES D-F; ingest-engine §5

## When to Use

- Ambiente com entrega TI limpa/interpolada
- Aceitar Excel quando TI atrasar (não bloqueia MVP)
- Registrar no manifesto qual `source_kind` venceu

## Implementation

```text
resolve_historical_source():
  if ti_tables_reachable() and ti_schema_ok():
      return Source(kind=ti_table, uri=...)
  if excel_exists():
      log warning "TI_MISSING_USING_EXCEL_FALLBACK"  # informativo local
      return Source(kind=excel, uri=...)
  raise Signal(INGEST_SOURCE_MISSING)
```

SLA de republicação TI (D-G) é operacional; não entra no path crítico do build.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `prefer_ti` | true | Ordem de resolução |
| `excel_fallback` | true | MVP |
| `block_without_ti` | false | Nunca no MVP |

## Example Usage

Manifesto: `source_kind: excel` + motivo fallback TI ausente.

## See Also

- [excel-qm-processo.md](excel-qm-processo.md)
- `docs/kb/gifi-domain/concepts/closed-decisions.md`

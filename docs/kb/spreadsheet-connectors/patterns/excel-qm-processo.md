# Excel QM×Processo Reader

> **Purpose**: Ler a base consolidada de referência do MVP  
> **Validated**: 2026-07-09  
> **Fonte**: PRD §3.1; ingest-engine dependência externa

## When to Use

- TI ainda não entregou base interpolada (D-F)
- Reprocesso offline a partir do Excel oficial
- Validação de schema contra amostra histórica

## Implementation

```python
# Contrato operacional (nível KB — implementação em src/)
REQUIRED_HINTS = [
    "data_processo", "turno", "Produção_Digestor",
    "volume", "mix_pct_or_volumes_by_site", "DB_SGF",
]

def read_qm_processo(path: str) -> dict:
    """Retorna {frame_ref, batch_identity, parse_warnings}."""
    # 1) abrir aba de dados (nome muda → registrar)
    # 2) tipar datas/números; não imputar aqui (I3 faz)
    # 3) calcular source_hash do arquivo
    # 4) inferir period_start/end de data_processo
    # 5) emitir INGEST_SOURCE_MISSING se ilegível
    ...
```

Período observado na referência: 2018-04 a 2025-10 (~7.573 turnos).

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `engine` | pandas/openpyxl | Leitor |
| `fail_on_missing_sheet` | true | Bloqueante |
| `infer_period` | true | min/max data_processo |

## Example Usage

Lote Excel com hash H1 entra em I2; se schema ok, segue para I3.

## See Also

- [ti-interpolated-fallback.md](ti-interpolated-fallback.md)
- [../concepts/batch-identity.md](../concepts/batch-identity.md)

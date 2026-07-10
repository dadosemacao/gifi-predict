# Remediation Cycle

> **Purpose**: Fluxo padrão quando ingestão histórica falha ou degrada  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §3

## When to Use

- Sinais bloqueantes no path histórico
- `ACCEPT_DATA_REJECT` da Camada 4
- Pedido de reprocesso (nova janela / agregação)

## Implementation

```text
1. DETECTAR   → sinal + log
2. ISOLAR     → quarentena; backbone não consome artefato novo
3. DIAGNOSTICAR → manifesto + amostra de violação
4. REMEDIAR   → fonte / regra / mapeamento (humano)
5. REPROCESSAR → novo lote, novo hash/versão
6. PUBLICAR   → só se I2+I3 ok
7. REGISTRAR  → evidência antes/depois + motivo + responsável
```

Regra: last-good nunca é sobrescrita por lote em quarentena.

## Configuration

| Signal type | Publish? | Next |
|-------------|----------|------|
| Bloqueante | Não | Ciclo completo |
| Aviso admitido | Sim + flag | Confiança decide |
| Info | Sim | Manifesto |

## Example Usage

Fonte com unidade g/cm³ → `INGEST_UNIT_FAIL` → quarentena → TI republica kg/m³ → reprocesso com novo `source_hash`.

## See Also

- [../concepts/signal-catalog.md](../concepts/signal-catalog.md)
- [warning-admissibility.md](warning-admissibility.md)

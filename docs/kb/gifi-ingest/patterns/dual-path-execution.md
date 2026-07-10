# Dual-Path Execution

> **Purpose**: Separar batch histórico de validação online de cenário  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §1.1

## When to Use

- Proteja SLA de UI (segundos) de quarentena/reprocesso
- Treino/holdout exigem lote assíncrono com remediação
- Evitar prometer “instantâneo” apoiado em pipeline batch

## Implementation

```text
Path Histórico (batch):
  I1 → I2 → I3 → I4 → I5
  + quarentena + remediação humana + novo hash

Path Cenário (online síncrono):
  Upload → I1 → I2 leve (schema, unidades, mix, faixas)
  → aceito: infer_features | rejeitado: motivo UI
  SEM quarentena / reprocesso / remediação no loop
```

## Configuration

| Setting | Histórico | Cenário |
|---------|-----------|---------|
| Latência | min–horas | segundos |
| Remediação §3 | Sim | Não |
| Status publish | `published_*` | validação síncrona |

## Example Usage

UI Modo A com mix soma 1.05 → `INGEST_SCENARIO_REJECT` em < poucos segundos, sem tocar last-good de treino.

## See Also

- [remediation-cycle.md](remediation-cycle.md)
- `docs/kb/gifi-domain/patterns/scenario-template-contract.md`

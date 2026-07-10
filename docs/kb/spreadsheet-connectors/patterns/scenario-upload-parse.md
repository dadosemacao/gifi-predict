# Scenario Upload Parse

> **Purpose**: Parse leve síncrono de planilha de cenário (path online)  
> **Validated**: 2026-07-09  
> **Fonte**: ingest-engine §1.1; template L1

## When to Use

- Upload UI Modo A/B
- Validar contra `template_cenario_vN` (não reinventar schema na UI)
- Devolver aceito/`infer_features` ou rejeição legível

## Implementation

```text
online_validate(file):
  1. parse sheet → rows (timeout curto)
  2. match template_version
  3. check required columns + types + units
  4. check mix sum ±0.02
  5. check mode A/B injection rules
  6. return ACCEPT → handoff I3 leve / infer_features
     or REJECT → INGEST_SCENARIO_REJECT + motivo PT-BR
```

Não executar: quarentena, imputação pesada de histórico, reprocesso.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_rows` | (definir) | Proteção UI |
| `timeout_s` | baixo | SLA segundos |
| `template_owner` | gifi-domain | Contrato |

## Example Usage

Modo A com `carga_alcalina` preenchida → rejeitar com texto claro.

## See Also

- `docs/kb/gifi-domain/patterns/scenario-template-contract.md`
- `docs/kb/gifi-ingest/patterns/dual-path-execution.md`

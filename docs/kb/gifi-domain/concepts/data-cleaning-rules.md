# Data Cleaning Rules

> **Purpose**: Regras numéricas que o Ingest (I2/I3) deve aplicar ao histórico  
> **Confidence**: 0.95  
> **Validated**: 2026-07-09  
> **Fonte**: PRD §3.2; `REFERENCIA_FAIXAS_OPERACIONAIS.md` D-02/D-07

## Overview

Estas regras são contrato da Camada 1. Quebra = sinal bloqueante no Ingest (exceto avisos catalogados). Unidade oficial de densidade é kg/m³.

## The Concept

```yaml
filter_training:
  rule: exclude_if_producao_digestor_lt_1000
  signal: INGEST_FILTER_INFO

density_unit:
  official: kg_per_m3
  forbidden: g_per_cm3

schema_db_range:
  min: 350
  max: 650
  action: alert_or_block_per_ingest_matrix

impute_db_lab:
  formula: "DB_LAB = 0.985 * DB_SGF"
  when: DB_LAB is null and DB_SGF is not null
  flag: db_origin = proxy
  obsolete_factor: 0.88

mix_sum:
  columns: [pct_A, pct_B, pct_C, pct_D, pct_MG]
  target: 1.0
  tolerance: 0.02
```

## Quick Reference

| Check | Pass | Fail signal |
|-------|------|-------------|
| Unidade | kg/m³ | `INGEST_UNIT_FAIL` |
| Mix soma | ∥sum−1∥ ≤ 0.02 | `INGEST_MIX_FAIL` |
| DB fora [350,650] | tratado ou bloqueio | ver matriz warnings |
| Proxy DB | flag `proxy` | `INGEST_PROXY_DB` |

## Common Mistakes

### Wrong

```python
db_lab = 0.88 * db_sgf  # legado
```

### Correct

```python
db_lab = 0.985 * db_sgf
db_origin = "proxy"
```

## Related

- [mix-feature-layers.md](mix-feature-layers.md)
- [../specs/domain-rules.yaml](../specs/domain-rules.yaml)
- `docs/kb/gifi-ingest/concepts/signal-catalog.md`

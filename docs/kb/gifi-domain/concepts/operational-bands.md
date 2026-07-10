# Operational Bands

> **Purpose**: Faixas oficiais e fator DB 0,985 (SSOT normativo)  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §3.5; `REFERENCIA_FAIXAS_OPERACIONAIS.md`

## Overview

Zonas Ótima / Aceitável / Crítica + âncora p50. Unidade de densidade: **kg/m³**.  
Imputação Lab: `DB_LAB = 0,985 × DB_SGF` (fator 0,88 obsoleto).

## The Concept

| Variável | Unidade | Ótima | Aceitável | Crítica | p50 |
|----------|---------|-------|-----------|---------|-----|
| DB_LAB | kg/m³ | 470–510 | 450–470 / 510–520 | <450 ou >520 | 483 |
| DB_SGF | kg/m³ | 475–505 | 465–475 / 505–515 | <465 ou >515 | 490 |
| Extrativo_AT | % | 1,5–2,1 | 2,1–2,45 | >2,45 | 1,89 |
| TPC | dias | 60–90 | 45–60 | <45 (verde) | 65 |
| Carga Alcalina | % Na₂O | 18,5–20,5 | 17,5–21,0 | >21 / <17,5 | 19,66 |
| Kappa | — | 16–18 | 15–18,5 | <15 ou >18,5 | 16,28 |
| % Casca | % | ≤1,0 | 1,0–1,5 | >1,5 | 0,80 |
| Volume | m³ | 7.500–9.500 | 6.000–11.000 | <6.000 | 8.669 |
| TSA | TSA/dia | 3.350–3.500 | 3.200–3.600 | <3.200* | 3.450 |

\*Paradas <1.000 fora do treino.

```python
DB_SCHEMA_RANGE = (350, 650)  # alerta schema
DB_LAB_FACTOR = 0.985         # nunca 0.88
TPC_GREEN = 45                # TPC < 45 = madeira verde
```

## Quick Reference

| Regra | Valor |
|-------|-------|
| Unidade DB | kg/m³ |
| Fator Lab | 0,985 |
| TPC verde | < 45 dias |
| Kappa no Elo 3 | processo fixo/estimado (não gerado pela cascata) |

## Common Mistakes

### Wrong

Usar g/cm³ ou fator 0,88; inventar faixas fora do YAML.

### Correct

Ler `specs/operational-ranges.yaml`; classificar zona; citar âncora p50 se útil.

## Related

- [data-cleaning-rules.md](data-cleaning-rules.md)
- [../specs/operational-ranges.yaml](../specs/operational-ranges.yaml)

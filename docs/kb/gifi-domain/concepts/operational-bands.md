# Operational Bands

> **Purpose**: Faixas oficiais e fator DB 0,985 (SSOT normativo)  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Atualizado em**: 2026-07-13  
> **Fonte**: PRD §3.5; `REFERENCIA_FAIXAS_OPERACIONAIS.md`

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

## Cobertura das variáveis obrigatórias das APIs

As faixas empíricas abaixo descrevem os valores observados em `primeira_base.csv`; elas **não são limites normativos**, não substituem as zonas oficiais acima e não devem, isoladamente, causar rejeição do request.

| Campo API | Variável | Faixa empírica | p50 empírico | Cobertura normativa |
|-----------|----------|----------------|--------------|---------------------|
| `carga_alcalina` | Carga Alcalina | 15,8–22,0 | ≈18,7 | Sim — consultar zonas oficiais acima |
| `kappa` | Kappa | 6,7–19,9 | ≈16,0 | Sim — consultar zonas oficiais acima |
| `db_sgf` | DB_SGF | 450–526 kg/m³ | ≈487 kg/m³ | Sim — consultar zonas oficiais acima |
| `secura_pct` | Secura | 46–71% | ≈62% | Não definida no SSOT normativo |
| `casca_pct` | % Casca | 0,14–2,44% | ≈0,84% | Sim — consultar zonas oficiais acima |
| `extrativo_total` | Extrativo Total | 1,75–6,19 | ≈3,5 | Não definida no SSOT normativo |
| `extrativo_sgf` | Extrativo SGF | 2,94–5,85 | ≈3,96 | Não definida no SSOT normativo |
| `tpc` | TPC | 24–185 dias | ≈59 dias | Sim — consultar zonas oficiais acima |
| `idade` | Idade | 5,4–10,1 anos | ≈6,7 anos | Não definida no SSOT normativo |

**Cobertura:** 5 das 9 variáveis obrigatórias possuem zonas normativas. Para `secura_pct`, `extrativo_total`, `extrativo_sgf` e `idade`, os intervalos apresentados são somente descritivos da base histórica.

**Fonte empírica:** `docs/api/DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md`, seção 3.1.

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
- [Dicionário das APIs Forecast e Predict-TSA](../../../api/DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md)

# Validação do Imputer de Extrativo_AT (Elo 1)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Fonte L2:** `2026-07-10T07:35:10Z` (antes) → `2026-07-13T09:33:13Z` (enriquecido)

## 1. Qualidade do imputer

| Métrica | Valor (p.p. de Extrativo_AT) |
|---------|------------------------------|
| MAE CV temporal (train medido) | 0.291 |
| MAE holdout medido (428 linhas) | 0.304 |
| MAE baseline (média do train) | 0.261 |
| Ganho vs baseline | -16.4% |

Imputer treinado em 2097 linhas medidas do treino.

## 2. Cobertura antes/depois

| Split | Antes | Depois |
|-------|-------|--------|
| train | 2097/7064 (29.7%) | 7064/7064 (100%) |
| holdout | 428/500 (85.6%) | 100% |

## 3. Distribuição por origem (train enriquecido)

| Origem | N | Média | Desvio | p05 | p50 | p95 |
|--------|---|-------|--------|-----|-----|-----|
| medido | 2097 | 1.892 | 0.384 | 1.290 | 1.880 | 2.570 |
| estimado | 4967 | 1.801 | 0.218 | 1.465 | 1.788 | 2.184 |

Faixa operacional de referência: ótima 1,5–2,1; aceitável 2,1–2,45; crítico >2,45.

## 4. Gráfico

![Validação do imputer](graphics/extrativo_imputer_validation.png)

## 5. Leitura

- O imputer **não supera** o baseline (média) no holdout (MAE 0.304 vs 0.261; -16.4%). Mix + idade têm baixo poder preditivo para Extrativo_AT — a imputação entrega **cobertura** (100%) mas os valores estimados ficam próximos da média, com baixa informação marginal. Alternativas: usar imputação por média/mediana condicional, incorporar variáveis lab/florestais mais correlacionadas, ou preferir OOF stack na Camada 3 em vez de imputar no L2.
- A distribuição estimada tende a ser mais concentrada em torno da mediana (regressão à média típica de RF), o que reduz a cauda crítica >2,45.
- Recomenda-se monitorar MAE por `extr_origin` a cada re-treino da cascata e revisitar o preenchimento quando a cobertura lab do histórico aumentar.

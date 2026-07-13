# Imputação de `Extrativo_AT` no Ingest (Elo 1)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Camada:** 2 (Ingest) — com efeito na Camada 3 (Simulação)
**Status:** implementado e validado (Excel L2)

---

## 1. Contexto e objetivo

`Extrativo_AT` (extrativos álcool-toluol) é detrator crítico e alvo do Elo 1 da
cascata. No L2 histórico, ~70% das linhas de treino não tinham medição lab
(gargalo de dados do Elo 3). O objetivo desta entrega é **preencher
`Extrativo_AT` quando ausente**, com rastreabilidade de origem, e medir o
impacto real no MAE.

Decisão do stakeholder (registrada): imputação na **Camada 2 (Ingest)** via
modelo, escopo **completo** (mecanismo + re-treino + validação) e publicação da
coluna `extr_origin`.

## 2. O que foi implementado

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| Imputer | `src/ingest/transform/imputation.py` | `fit_extrativo_imputer` / `apply_extrativo_imputer` / `impute_extrativo_at` (RandomForest, mix + idade) |
| Wiring | `src/ingest/transform/pipeline.py` | executa após features de mix, antes da meta diária |
| Proveniência | coluna `extr_origin` (`medido` / `estimado`) | publicada no Parquet L2 |
| Sinal | `INGEST_PROXY_EXTR` | catálogo + matriz de warnings + guard `admit_if` |
| Config | `config/ingest.yaml` → `extr_impute` | enabled, min_train_rows, random_state, range |
| Backfill | `scripts/backfill_extrativo_l2.py` | republica L2 enriquecido |
| Validação | `scripts/validate_extrativo_imputer.py` | MAE + gráfico |
| Testes | `tests/ingest/test_transform.py` | preenchimento e esparsidade |

### Disciplina temporal (anti-vazamento)

O imputer é treinado **apenas** com linhas medidas da janela de treino
(`data_processo <= train_cutoff`). O holdout nunca entra no fit; suas linhas
ausentes são preenchidas por um modelo que não as viu (comportamento Modo A).

### Fronteira arquitetural

O imputer é **self-contained no Ingest** (usa `sklearn` diretamente, sem
importar `simulation.*`), preservando o sentido de dependência
Ingest → Simulação. Isso relaxa conscientemente a regra "Ingest não treina
modelo" da skill, por decisão explícita do stakeholder.

## 3. Resultados (Excel L2)

### Cobertura

| Split | Antes | Depois |
|-------|-------|--------|
| train | 2 097/7 064 (29,7%) | 7 064/7 064 (100%) — 4 967 estimadas |
| holdout | 428/500 (85,6%) | 500/500 (100%) — 72 estimadas |

### Qualidade do imputer

| Métrica | Valor (p.p.) |
|---------|--------------|
| MAE CV temporal (train medido) | 0,291 |
| MAE holdout medido (428 linhas) | 0,304 |
| MAE baseline (média do train) | 0,261 |
| Ganho vs baseline | **−16,5%** (não supera a média) |

### Efeito no MAE de TSA (re-treino `direct_tsa`)

| Cenário | MAE holdout |
|---------|-------------|
| Antes (candidato `direct_tsa` 2026-07-10) | 90,83 |
| Depois (L2 enriquecido, campeão xgboost) | **89,43** |

Ganho ~1,5%; permanece acima do gate 56 (`release_ok=false`).

## 4. Leitura crítica

- **Cobertura ≠ sinal.** O imputer atinge 100% de cobertura, mas mix + idade têm
  baixo poder preditivo para `Extrativo_AT`: no holdout ele **não supera a média**.
  As estimativas concentram-se em 1,5–2,1, perdendo a cauda crítica (>2,45) —
  ver `graphics/extrativo_imputer_validation.png`.
- **Impacto pequeno no TSA** (~1,5%), coerente com o diagnóstico anterior
  (`DIAGNOSTICO_MAE_ELO3.md`): o gargalo do Elo 3 não é a ausência de extrativo,
  mas o shift de distribuição e a informação limitada das features atuais.

## 5. Próximos passos sugeridos

1. Incorporar variáveis lab/florestais mais correlacionadas ao Elo 1 (hoje
   `Extrativo_SGF` tem ρ ≈ 0,07 — insuficiente).
2. Comparar com imputação por mediana condicional (por faixa de mix/idade).
3. Reavaliar se a imputação deve ocorrer no L2 (cobertura) ou permanecer como
   OOF stack na Camada 3 (sinal sem contaminar o artefato publicado).
4. Monitorar MAE por `extr_origin` a cada re-treino e revisar quando a cobertura
   lab do histórico aumentar.

## 6. Reprodução

```bash
# Backfill do L2 publicado
PYTHONPATH=src python scripts/backfill_extrativo_l2.py --l2-root data/l2_excel_validation

# Validação (MAE + gráfico)
PYTHONPATH=src python scripts/validate_extrativo_imputer.py

# Re-treino da cascata com L2 enriquecido
PYTHONPATH=src python -m simulation.cli train --l2-root data/l2_excel_validation
```

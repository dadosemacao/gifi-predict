# Diagnóstico de Modelagem — MAE Elo 3 e Cascata TSA

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Status:** Referência para análise futura  
**Gate normativo:** `MAE_holdout ≤ 56 TSA/dia` (Matriz A)  
**Base de validação:** `data/l2_excel_validation` (Excel QM × Processo, `2026-07-10T07:35:10Z`)

---

## 1. Objetivo deste documento

Registrar o estado da modelagem após iterações de tuning (GridSearchCV), stacking OOF e inclusão de novas famílias (XGBoost, LightGBM, CatBoost, ExtraTrees, Ridge, Lasso), com evidências quantitativas e um plano de melhoria priorizado para retomada futura.

---

## 2. Resumo executivo

| Item | Valor |
|------|-------|
| Melhor `mae_tsa_cascade` (honesto, holdout 500 linhas) | **94,31** → **96,70** (última corrida OOF) |
| Gate MAE ≤ 56 | **Não atingido** (`release_ok=false`) |
| Gargalo principal | **Elo 3** (~93–96 t/dia); Elo 1/2 estáveis (~0,3 / ~0,8) |
| Alavancagem de tuning adicional | **Baixa** (~2–5 t/dia estimados) |
| Alavancagem de dados + features + alinhamento pipeline | **Alta / crítica** |

**Conclusão:** o teto atual não é limitado por falta de algoritmos, e sim por **cobertura de rótulos**, **shift temporal no holdout**, **sinal fraco nas features lineares** e **desalinhamento treino (OOF) vs inferência (Modo A)**.

---

## 3. Histórico de experimentos

### 3.1 Baseline inicial (sem tuning)

| Métrica | Valor |
|---------|-------|
| Campeões | baseline / randomforest / elasticnet |
| `mae_tsa_cascade` | **94,79** |
| `mae_tsa_isolated` (Elo 3) | 91,67 |
| Linhas treino Elo 3 (com `Extrativo_AT` observado) | ~2 094 |

**Candidato:** `models/candidates/2026-07-10T08:08:31.339996Z/`

### 3.2 GridSearch + seleção por cascata (sem OOF)

| Métrica | Valor |
|---------|-------|
| Campeões | randomforest / randomforest / elasticnet |
| `mae_tsa_cascade` | **94,31** |
| Linhas treino Elo 3 | ~2 094 |

**Candidato:** `models/candidates/2026-07-10T09:54:11.371893Z/`

### 3.3 Stacking OOF + 9 famílias Elo 3

| Métrica | Valor |
|---------|-------|
| Campeões | randomforest / randomforest / **catboost** |
| `mae_tsa_cascade` | **96,70** |
| `mae_tsa_isolated` (Elo 3) | 95,74 |
| Linhas treino Elo 3 (com OOF) | **6 997** (vs ~2 094 sem OOF) |
| Melhor CV MAE (OOF, ElasticNet) | **64,1** |
| Gap CV → holdout | ~33 t/dia |

**Candidato:** `models/candidates/2026-07-10T10:54:42.849161Z/`

**Meta OOF registrada:**

- `folds_run`: 3 de 5 (folds iniciais falham por poucas linhas com rótulo Elo 1)
- `fallback_extr_rows`: 3 533 (~50% das linhas usaram fallback in-sample, não OOF puro)
- `oof_extr_rows` / `oof_carga_rows`: 7 064 (após merge com observado + fallback)

### 3.4 Comparativo de famílias (CV OOF vs holdout cascata)

| Família | CV MAE (OOF) | Selecionada no holdout? |
|---------|--------------|------------------------|
| ElasticNet | **64,1** | Não |
| Lasso | 64,2 | Não |
| Ridge | 65,9 | Não |
| ExtraTrees | 65,4 | Não |
| CatBoost | 66,7 | **Sim (campeã)** |
| RandomForest | 68,7 | Não |
| HistGradientBoosting | 70,3 | Não |
| LightGBM | 70,5 | Não |
| XGBoost | 71,8 | Não |

---

## 4. Evidências da base L2 (Excel)

### 4.1 Escala TSA

| Conjunto | Média | Desvio-padrão | Min | Max |
|--------|-------|---------------|-----|-----|
| Train (7 064) | 3 410,2 | 95,4 | 3 001,1 | 3 600,0 |
| Holdout (500) | 3 468,7 | 120,6 | 3 011,2 | 3 650,0 |

Holdout **+58,5 t/dia** acima da média do train (regime 2025-05 → 2025-10).

### 4.2 Missingness no train

| Coluna | NA | % |
|--------|----|---|
| `Extrativo_AT` | 4 967 / 7 064 | **70,3%** |
| `Carga_Alcalina` | 0 | 0% |
| `DB_LAB`, `TPC`, `VMI` | 0 | 0% |
| `Casca_pct` | 2 632 | 37,3% |
| `Extrativo_SGF` | 882 | 12,5% |

### 4.3 Shift holdout vs train (principais variáveis)

| Variável | Δμ (hold − train) | Observação |
|----------|-------------------|------------|
| `TSA_dia` | **+58,5** | Produção mais alta no holdout |
| `DB_LAB` | **−15,1** | Densidade mais baixa no holdout |
| `pct_ABC` | +0,15 | Mix mais concentrado em ABC |
| `mix_entropy` | −0,24 | Menor diversidade de mix |
| `Carga_Alcalina` | −1,5 | Carga ligeiramente menor |
| `TPC` | +4,9 | TPC um pouco maior |

### 4.4 Correlação linear com TSA (train, linhas com `Extrativo_AT` observado)

| Feature | ρ |
|---------|---|
| `Carga_Alcalina` | −0,31 |
| `Extrativo_AT` | −0,18 |
| `pct_ABC` | +0,24 |
| `Volume_m3` | +0,18 |
| `TPC` | +0,20 |
| `DB_LAB` | −0,10 |
| `VMI` | +0,06 |
| `Kappa` | +0,07 |

Relações **fracas em linear**; PRD e `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` indicam **não-linearidades** (curva em U do DB, zonas TPC/Carga/Extrativo) ainda não codificadas em `elo_specs`.

### 4.5 Origem dos dados (`db_origin`)

| Origem | Linhas | Com `Extrativo_AT` observado | TSA médio |
|--------|--------|------------------------------|-----------|
| lab | 6 472 | 2 076 (32%) | 3 410,4 |
| proxy | 592 | 21 (3,5%) | 3 408,7 |

A maior parte do histórico **lab** não traz extrativo medido — limitação estrutural do L2, não do simulador.

### 4.6 Baselines de referência (holdout)

| Baseline | MAE |
|----------|-----|
| Prever média do train | **108,7** |
| Prever mediana do train | **88,4** |
| Modelo atual (melhor cascata) | **94,3 – 96,7** |

O modelo supera a média (~13 t/dia), mas fica **próximo ou pior** que a mediana — ganho preditivo modesto.

---

## 5. Diagnóstico por camada

### 5.1 Elo 1 (Extrativo_AT)

- MAE holdout ~0,26–0,30 t/dia — **OK**
- RandomForest ligeiramente melhor que baseline na cascata
- Treino limitado a ~2 097 linhas com rótulo observado

### 5.2 Elo 2 (Carga_Alcalina)

- MAE holdout ~0,79 t/dia — **OK**
- Não é gargalo

### 5.3 Elo 3 (TSA_dia)

- MAE isolado ~92–96 t/dia — **gargalo**
- Cascata ≈ isolado (erro propagado de Elo 1/2 é mínimo)
- Com OOF: CV ~64 vs holdout ~97 → **generalização fraca**

### 5.4 Pipeline treino vs inferência

| Aspecto | Treino (OOF) | Inferência holdout (Modo A) |
|---------|--------------|----------------------------|
| `Extrativo_AT` / `Carga_Alcalina` | OOF + 50% fallback | Predição cascata pipes finais |
| Distribuição das features upstream | Diferente | Diferente |
| Efeito | CV otimista | Holdout pior que CV |

---

## 6. Onde melhorar (priorizado)

### Prioridade 1 — Dados / Ingest (maior alavancagem)

1. **Recuperar ou imputar `Extrativo_AT` no L2** (lab + proxy SGF; hoje 70% NA).
2. **Validar alinhamento temporal** turno ↔ processo entre elos.
3. **Revisar cobertura `db_origin=proxy`** (592 linhas, quase sem extrativo).
4. Garantir holdout com mesma qualidade de schema que o train.

**Responsável sugerido:** Camada 2 — `gifi-ingest-engineer`.

### Prioridade 2 — Feature engineering de domínio

Features documentadas em `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` ainda **fora** de `config/simulation.yaml` → `elo_specs.elo3`:

| Feature proposta | Justificativa |
|------------------|---------------|
| `DB_LAB²` ou centrado em 490 | Curva em U (ρ linear ≈ 0) |
| Zonas TPC (<45 crítico; 60–90 ótimo) | ρ +0,18 a +0,25 |
| Zonas Carga (>21 crítica) | ρ −0,23 a −0,37 |
| Flag Extrativo > 2,45% | Zona crítica empírica |
| Bins VMI (`vmi_le_021`, `vmi_021_025`, `vmi_gt_025`) | Já existem no parquet |
| `Secura_pct`, `Idade`, `dom_*` | Colunas L2 não usadas |
| Interações (Extr×Carga, DB×Extr, TPC×VMI) | Efeitos combinados |

### Prioridade 3 — Alinhar treino e inferência

1. Treinar Elo 3 com **Modo A consistente** (mesma lógica do holdout), não OOF misturado com fallback.
2. Completar OOF: walk-forward ou garantir cobertura OOF em **100%** das linhas (eliminar 3 533 fallbacks).
3. Selecionar campeão Elo 3 por **CV alinhada ao Modo A**, não só por MAE cascata no holdout (evitar CatBoost CV 66,7 vs EN CV 64,1).

### Prioridade 4 — Arquitetura alternativa

| Opção | Trade-off |
|-------|-----------|
| Elo 3 **direct** (sem cascata para TSA) | Menos erro propagado; perde narrativa Modo A/B |
| Modelo **residual** (TSA − baseline por mix/DB) | Captura desvio em relação à média |
| **Multi-output** ou single model | Uma fronteira vs três elos |
| Segmentar MAE por mês / turno / `db_origin` | Identificar subconjuntos recuperáveis |

### Prioridade 5 — Meta e validação

- MAE ≤ 56 ≈ **57% de 1σ** (σ ≈ 98 t/dia) — ambicioso em holdout com shift +58 t/dia.
- Avaliar com stakeholder se gate permanece ou se exige **MAE segmentado** / intervalo.
- Decompor erro holdout por variável de shift (`DB_LAB`, `pct_ABC`, `mix_entropy`).

---

## 7. Roadmap sugerido

```
[Dados L2: Extrativo_AT + cobertura]
        ↓
[Features domínio no elo_specs]
        ↓
[Treino Modo A = inferência (sem OOF/fallback misto)]
        ↓
[Experimento Elo 3 direct vs cascata]
        ↓
[Tuning famílias + GridSearch refinado]
        ↓
[Gate MAE ≤ 56 — Matriz A]
```

---

## 8. Configuração atual (referência)

Arquivo: `config/simulation.yaml`

```yaml
tuning:
  enabled: true
  cv_folds: 5
  elo3_oof_stack: true
  elo3_cascade_fill: false
  select_by_cascade: true
  elo3_families:
    - elasticnet
    - ridge
    - lasso
    - randomforest
    - extratrees
    - histgradientboosting
    - xgboost
    - lightgbm
    - catboost
```

Implementação OOF: `src/simulation/models/oof_stack.py`  
Famílias: `src/simulation/models/families.py`  
GridSearch: `src/simulation/models/grid_search.py`

---

## 9. Próximas ações (quando retomar)

- [ ] Diagnóstico Ingest: por que 70% do train lab não tem `Extrativo_AT`
- [ ] Implementar pacote de features de domínio no Elo 3
- [ ] Refatorar treino Elo 3 para Modo A consistente (sem mismatch OOF)
- [ ] Completar OOF walk-forward (zero fallback)
- [ ] Experimento Elo 3 direct vs cascata com mesmas features
- [ ] Decomposição MAE holdout por mês e `db_origin`
- [ ] Revisão gate 56 com stakeholder se gap persistir após L2 + features

---

## 10. Referências

| Documento | Uso |
|-----------|-----|
| `docs/PRD_GIFI_v1.1.md` | Gate MAE, cascata, Modo A/B |
| `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` | Faixas, zonas, correlações |
| `docs/sketch/DIVERGENCIAS_E_MITIGACAO_GIFI.md` | Decisões em aberto |
| `docs/CHANGELOG.md` | Versões 0.2.2 e 0.2.3 (tuning + OOF) |
| `.claude/sdd/features/DEFINE_ACCEPTANCE_GATE.md` | Matriz A∧B∧C |

---

## 11. Changelog deste documento

| Data | Alteração |
|------|-----------|
| 2026-07-10 | Criação — consolidação pós-experimentos tuning, OOF e 9 famílias |

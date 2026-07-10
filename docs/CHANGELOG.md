# Changelog — GIFI Predict

**Autor:** Emerson Antônio

---

## [0.3.0] — 2026-07-10

### Adicionado

- **Gate de Aceite (Camada 4):** pacote `src/acceptance/` — Matrizes A∧B∧C, política `release_ok` / `demo_mode`, promoção de campeão.
- CLI `accept` (`run --run-id`, `report --run-id`).
- Configuração `config/acceptance.yaml` e cenários versionados em `config/acceptance_scenarios/` (anchor, TC-03/05, TM-01…05, TC-09/10).
- Relatórios em `reports/acceptance/{run_id}/acceptance_report.json`.
- Campeão produtivo em `models/champion/{run_id}/` + `current_champion.json` (somente quando `release_ok=true`).
- Testes `tests/acceptance/` (14 casos, incluindo smoke Excel L2 `@slow`).
- Dependência `shap>=0.44` (Matriz C — top-3 detratores).
- **SDD:** Camada 4 arquivada em `.claude/sdd/archive/ACCEPTANCE_GATE/`.

### Adicionado (Camada 3 — pós-ship)

- **`simulate infer --run-id`** e **`simulate evaluate --run-id`** — carregam candidato L3 sem depender de `current_candidate.json`.
- **Explainability no manifesto L3:** coeficientes (ElasticNet/Ridge/Lasso) e `feature_importances` (RF, ExtraTrees, XGB, LGBM, CatBoost) via `extract_explainability`.
- Testes `tests/simulation/test_infer_pipeline.py`, `tests/simulation/test_explainability.py`.

### Validado (Excel L2)

- Smoke `accept run --run-id <candidato OOF>`:
  - `matriz_a=false` (MAE ~94–97 > 56)
  - `matriz_b=false` (MVP TC-03/05 + TM)
  - `matriz_c=true`
  - `release_ok=false`, `demo_mode=true`
- Suite pytest (`-m "not slow"`): **50 passed** (ingest + simulation + acceptance).

### Débito conhecido

- Gate completo **A∧B∧C verde** depende de iteração L2/L3 (MAE ≤ 56).
- Matriz B MVP cobre TC-03/05 + TM-01…05; TC-01…02, TC-04, TC-06…08 ficam para Marco 2.
- AT-011 (p95 infer < 5s) não automatizado.

---

## [0.2.3] — 2026-07-10

### Documentação

- **`docs/analysis/RELATORIO_DADOS_ENGENHARIA_VARIAVEIS.md`** — relatório de problemas estruturais por variável para engenharia de dados.
- **`docs/analysis/DIAGNOSTICO_MAE_ELO3.md`** — diagnóstico consolidado (MAE ~96 vs gate 56), evidências L2, experimentos e roadmap de melhoria.

### Adicionado

- **Stacking OOF (Elo 1→2→3):** `enrich_elo3_oof_features` preenche `Extrativo_AT` / `Carga_Alcalina` com predições out-of-fold temporais, expandindo treino Elo 3 para ~7 000 linhas com `TSA_dia` sem vazamento de holdout.
- **Novas famílias Elo 3:** XGBoost, LightGBM, CatBoost, ExtraTrees, Ridge, Lasso (+ grids GridSearchCV).
- Dependências: `xgboost`, `lightgbm`, `catboost`.
- Teste `tests/simulation/test_oof_stack.py`.

### Alterado

- `config/simulation.yaml`: `elo3_oof_stack: true` e lista completa de famílias para tuning.
- Falha em uma família durante GridSearch não interrompe as demais (registrada em `tuning_meta`).

### Validado (Excel L2 + OOF)

- Treino Elo 3 expandido: **6 997 linhas** (vs ~2 094 sem OOF).
- Campeão cascata: **CatBoost** (RF / RF / CatBoost) — `mae_tsa_cascade = 96,70` (`release_ok=false`).
- Melhor CV MAE (OOF): ElasticNet **64,1**; holdout honesto permanece acima do gate 56.

---

## [0.2.2] — 2026-07-10

### Adicionado (modelagem Elo 3)

- **GridSearchCV + TimeSeriesSplit** para Elo 3 (`elasticnet`, `randomforest`, `histgradientboosting`).
- **Pools configuráveis** em `config/simulation.yaml`: `grid_search_pool`, `training_pool`, `train_fraction` (80/20 temporal).
- **`cascade_training`:** preenchimento opcional de `Extrativo_AT` / `Carga_Alcalina` via predições Modo A para ampliar linhas de treino Elo 3.
- **Seleção de campeão por `mae_tsa_cascade`** (busca conjunta elo1 × elo2 × elo3 no holdout).
- **`n_jobs: -1`** no GridSearch para paralelização.

### Validado (Excel L2)

- Melhor candidato honesto: **MAE_TSA_cascade = 94,31** (campeões: RF / RF / EN).
- Gate **MAE ≤ 56** não atingido (`release_ok=false`).
- Gargalo: apenas ~2 094 linhas com `Extrativo_AT` observado para treino Elo 3; holdout 2025-05→10 permanece fora do fit.

---

## [0.2.1] — 2026-07-10

### Adicionado

- **SDD:** Camada 3 arquivada em `.claude/sdd/archive/SIMULATION_ENGINE/`.
- **Dev environment:** `scripts/setup_dev.sh`, `.python-version` (3.12), `uv.lock`, `requirements.txt`, `requirements-dev.txt`.
- **Toolchain:** `ruff` + `pytest-cov` em `[project.optional-dependencies].dev`.
- **Documentação:**
  - `docs/guides/DEV_ENVIRONMENT.md` — auditoria, setup, agentes, comandos.
  - `docs/adr/ADR-003-manifest-vs-mlflow.md` — decisão filesystem vs MLflow por marco.

### Alterado

- `README.md` — Camada 3, setup padronizado, estrutura atualizada.
- `tests/simulation/conftest.py` — import de fixture corrigido para venv isolado.

---

## [0.2.0] — 2026-07-10

### Adicionado

- **Motor de Simulação (Camada 3):** pacote `src/simulation/` — cascata Elo 1→2→3, champion por elo, Modo A/B.
- CLI `simulate` (`train`, `evaluate`, `infer`).
- Configuração `config/simulation.yaml`.
- Testes `tests/simulation/` (13 casos, incluindo smoke Excel L2).
- Empacotamento L3 em `models/candidates/{run_id}/` com manifesto JSON.

### Validado

- 26 testes pytest (ingest + simulation).
- Smoke `simulate train` com Excel L2: MAE_TSA_cascade ~94.79 (`release_ok=false`).

---

## [0.1.0] — 2026-07-10

### Adicionado

- **Ingest Engine (Camada 2):** pacote `src/ingest/` com pipeline I1–I5 (batch + online).
- CLI `ingest` (`batch`, `scenario-validate`, `scenario-publish`, `reprocess`).
- Configuração `config/ingest.yaml` e contratos KB em `docs/kb/gifi-ingest/`.
- Testes `tests/ingest/` (13 casos, incluindo Excel real 7.573 turnos).
- Documentação: `docs/diagrams/INGEST_ENGINE.md` (diagramas de classes e fluxo).
- README atualizado com instruções de setup e uso do ingest.

### Validado

- Excel `Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx`:
  - 7.064 linhas `train_features` + 500 `holdout_features`
  - `published_with_warnings` (`INGEST_PROXY_DB`)

### Arquivado (SDD)

- Feature INGEST_ENGINE em `.claude/sdd/archive/INGEST_ENGINE/`

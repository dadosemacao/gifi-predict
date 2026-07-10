# BUILD REPORT: Motor de Simulação (Camada 3 GIFI)

> Phase 3 — implementação concluída conforme DESIGN_SIMULATION_ENGINE.md v1.1

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SIMULATION_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (build-agent) |
| **DESIGN** | `.claude/sdd/features/DESIGN_SIMULATION_ENGINE.md` |
| **DEFINE** | `.claude/sdd/features/DEFINE_SIMULATION_ENGINE.md` |
| **Status** | Shipped |

---

## Summary

Implementada a **Camada 3 (Motor de Simulação)**: carga L2, guards, feature matrices, treino Baseline/ElasticNet/RandomForest por elo, seleção de champion heterogêneo, avaliação holdout (MAE/RMSE/WAPE), inferência Modo A/B, empacotamento atômico de candidatos e CLI `simulate`.

---

## Files Delivered

| # | File | Status |
|---|------|--------|
| 1 | `pyproject.toml` | Modified — sklearn, joblib, script `simulate`, name `gifi-predict` v0.2.0 |
| 2 | `config/simulation.yaml` | Created |
| 3–29 | `src/simulation/**` | Created (config, l2, features, metrics, models, cascade, package, pipeline, cli, observability) |
| 30 | `.gitignore` | Modified — `models/`, `logs/simulation/` |
| 31–38 | `tests/simulation/**` | Created — 13 testes + fixture `l2_mini` |

**Total:** 38 arquivos conforme manifesto DESIGN.

---

## Validation Results

| Check | Result |
|-------|--------|
| `pytest tests/simulation/` | 13 passed (incl. `@slow` Excel L2) |
| `pytest tests/` (full suite) | 26 passed |
| `simulate train --l2-root data/l2_excel_validation` | OK — 7.064 train, 500 holdout, ~4.7s |
| MAE_TSA cascade (Excel L2) | 94.79 — `release_ok=false` (gate > 56) |
| Champions (Excel L2) | elo1=baseline, elo2=randomforest, elo3=elasticnet |

---

## Acceptance Tests Coverage

| AT | Test | Status |
|----|------|--------|
| AT-001 | `test_train_pipeline`, `test_integration_l2` | Covered |
| AT-002 | `test_integration_l2` (holdout window) | Covered |
| AT-003 | `test_evaluate_pipeline` | Covered |
| AT-004 | `test_guard_schema_mismatch` | Covered |
| AT-005 | `test_guard_holdout_ineligible` | Covered |
| AT-006 | `test_mode_a_cascade` | Covered |
| AT-007 | `test_mode_b_injection` | Covered |
| AT-008 | `test_mode_a_rejects_injection` | Covered |
| AT-009 | Proxy DB em Elo 3 | Implicit via L2 real data |
| AT-010 | Elo 1b ausente | No code path — verified by design |
| AT-011 | infer p95 < 5s | Débito Marco 2 (não automatizado) |
| AT-012 | Manifesto L3 refs L2 | `test_train_pipeline` |
| AT-014 | Smoke Excel L2 | `test_integration_l2` @slow |
| AT-015 | `test_reproducibility` | Covered |

---

## Autonomous Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| `strict_scenario` flag | `False` em avaliação holdout cascade | Holdout histórico contém `Extrativo_AT`/`Carga_Alcalina` reais; Modo A em cenário continua rejeitando injeção |
| `run_id` com microssegundos | ISO UTC com fração | Evita colisão em `FileExistsError` em testes rápidos |
| RF `n_jobs=1` | Reprodutibilidade AT-015 | `n_jobs=-1` gerava drift numérico mínimo |
| `release_ok=false` | Não atualiza `current_candidate.json` | DESIGN Decision 7 — só promove pointer se gate informativo passar |
| Inferência com `pd.DataFrame` nomeado | Em vez de listas | Elimina warnings sklearn e alinha com fit |

---

## Known Limitations / Débito Marco 2

- MAE_TSA ~95 no Excel real — acima do gate 56; candidato empacotado mas sem pointer (esperado no MVP)
- AT-011 performance infer não automatizado
- Lock `fcntl` local-only (sem distribuído multi-host)
- SHAP / Matrizes B/C delegados à Camada 4

---

## CLI Usage

```bash
pip install -e ".[dev]"
simulate train --l2-root data/l2_excel_validation
simulate evaluate
simulate infer --cenario-id <id> --mode A
```

---

## Next Step

```bash
/ship .claude/sdd/features/DEFINE_SIMULATION_ENGINE.md
```

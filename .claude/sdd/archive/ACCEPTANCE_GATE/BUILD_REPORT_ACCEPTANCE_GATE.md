# BUILD REPORT: Gate de Confiança e Aceite (Camada 4 GIFI)

> Phase 3 — implementação concluída conforme DESIGN_ACCEPTANCE_GATE.md v1.0

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | ACCEPTANCE_GATE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (build-agent) |
| **DESIGN** | `.claude/sdd/features/DESIGN_ACCEPTANCE_GATE.md` |
| **DEFINE** | `.claude/sdd/features/DEFINE_ACCEPTANCE_GATE.md` |
| **Status** | Shipped |

---

## Summary

Implementado o **Gate de Confiança e Aceite (Camada 4)**: Matrizes A/B/C, política `A∧B∧C`, relatórios auditáveis, promoção de campeão produtivo e CLI `accept`. Integração direta com API da Camada 3 (`infer_dataframe`, `evaluate_holdout`, `load_candidate_pipes_by_run_id`).

---

## Files Delivered

| # | File | Status |
|---|------|--------|
| 1 | `pyproject.toml` | Modified — v0.3.0, `shap`, CLI `accept` |
| 2 | `config/acceptance.yaml` | Created |
| 3–13 | `config/acceptance_scenarios/*.yaml` | Created (anchor, TM-01…05, TC-03/05, TC-09/10) |
| 14–26 | `src/acceptance/**` | Created (config, l3, scenarios, matrices, policy, package, pipeline, cli) |
| 27–33 | `tests/acceptance/**` | Created — 14 testes |
| 34 | `.gitignore` | Modified — `reports/acceptance/`, `logs/acceptance/` |

**Total:** 34 arquivos conforme manifesto DESIGN.

---

## Validation Results

| Check | Result |
|-------|--------|
| `ruff check src/acceptance tests/acceptance` | OK |
| `pytest tests/ -m "not slow"` | **50 passed** |
| `accept run --run-id` (Excel L2) | OK — `matriz_a=false`, report gerado |
| `pytest tests/acceptance/test_accept_excel_slow.py` | `@slow` — MAE fail esperado |

---

## Acceptance Tests Coverage

| AT | Test | Status |
|----|------|--------|
| AT-ACC-001 | `test_accept_pipeline_produces_report` | Covered |
| AT-ACC-002/003 | `test_matriz_a_*`, `test_accept_excel_slow` | Covered |
| AT-ACC-004/005 | `test_matriz_b_*` | Covered |
| AT-ACC-006/007 | `test_matriz_c_*` | Covered |
| AT-ACC-008/013 | `test_combine_gate_partial_fail`, `test_demo_mode_*` | Covered |
| AT-ACC-009/010 | `test_champion_promotion_and_last_good` | Covered |
| AT-ACC-015 | `test_accept_pipeline_deterministic` | Covered |
| AT-ACC-011/012 | Guards em pipeline (integridade + holdout) | Implicit |

---

## Autonomous Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| TC-01…08 completos | MVP com TC-03/05 + TM + TC-09/10 | Reduz YAML inicial; extensível sem mudar código |
| TC-08 feature_check | Stub pass com nota | Validação de features permanece no Ingest/L2 |
| Matriz C baseline family | `permutation_importance` fallback | Família `baseline` nos fixtures de teste |
| Test Excel renomeado | `test_accept_excel_slow.py` | Evita colisão com `tests/ingest/test_integration_excel.py` |
| `recompute_matriz_a` default true | Produção | Gate autoritativo vs metrics L3 |

---

## Known Limitations / Débito Marco 2

- Matriz B completa TC-01…08 ainda não em YAML (só TC-03/05 + TM)
- Excel real: `matriz_a=false` (~94 MAE), `release_ok=false` — esperado
- Comparador multi-run de candidatos (SHOULD Marco 2)
- AT-ACC-014 wall-clock 15 min — não automatizado

---

## CLI Usage

```bash
pip install -e ".[dev]"
accept run --run-id 2026-07-10T10:54:42.849161Z --l2-root data/l2_excel_validation
accept report --run-id 2026-07-10T10:54:42.849161Z
```

---

## Next Step

**Shipped:** [SHIPPED_2026-07-10.md](./SHIPPED_2026-07-10.md)

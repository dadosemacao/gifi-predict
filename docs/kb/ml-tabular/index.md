# ML Tabular Knowledge Base (GIFI Cascade)

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.1

> **Purpose**: Supervised tabular ML for industrial cascade Elo1→2→3 — not RAG/GenAI  
> **Confidence**: 0.95 (PRD + scikit-learn MCP)  
> **MCP Validated**: 2026-07-09  
> **Sources**: PRD §4; analytical-backbone Camada 3–4; scikit-learn docs

## Quick Navigation

### Concepts (< 150 lines each)

| File | Purpose |
|------|---------|
| [concepts/cascade-regression.md](concepts/cascade-regression.md) | Elo 1→2→3 targets and features |
| [concepts/elasticnet-vs-rf.md](concepts/elasticnet-vs-rf.md) | Candidate families + baseline |
| [concepts/temporal-holdout.md](concepts/temporal-holdout.md) | Time split; no shuffle leakage |
| [concepts/stage-metrics.md](concepts/stage-metrics.md) | MAE/RMSE/WAPE per stage |
| [concepts/physics-constraints.md](concepts/physics-constraints.md) | Monotonicity / stress tests |

### Patterns (< 200 lines each)

| File | Purpose |
|------|---------|
| [patterns/train-select-champion.md](patterns/train-select-champion.md) | Train candidates → champion |
| [patterns/report-intermediate-mae.md](patterns/report-intermediate-mae.md) | Per-elo MAE reporting |
| [patterns/mode-a-b-inference.md](patterns/mode-a-b-inference.md) | Integration vs isolation |
| [patterns/artifact-packaging.md](patterns/artifact-packaging.md) | Release-gate packaging |
| [patterns/matriz-c-detractors.md](patterns/matriz-c-detractors.md) | Top-3 ΔTSA (SHAP / coef / permutation) |
| [patterns/inference-serving.md](patterns/inference-serving.md) | FastAPI upload → curves + detractors |

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Cascade** | Sequential regressors; error compounds |
| **Temporal holdout** | Train ≤2025-04; holdout 2025-05→10 |
| **Champion** | Best MAE only if Matriz B∧C pass |
| **Mode A/B** | End-to-end vs injected intermediates |

## Agent Usage

| Agent | Primary Files | Use Case |
|-------|---------------|----------|
| `gifi-simulation-engineer` | All | Motor / cascade |
| `gifi-acceptance-engineer` | stage-metrics, physics, champion | Gate A/B/C |
| `python-developer` | patterns/* | Implementation |
| `test-generator` | physics, metrics | TC suites |

## Quick Reference

- [quick-reference.md](quick-reference.md)

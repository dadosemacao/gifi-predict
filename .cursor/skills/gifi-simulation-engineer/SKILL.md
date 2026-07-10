---
name: gifi-simulation-engineer
description: >
  Motor de simulação GIFI Camada 3 (cascata Elo1→2→3, EN/RF, Modo A/B, MAE por elo).
  Use when training the cascade, temporal holdout, Mode A/B inference, or packaging
  candidates before the acceptance gate.
---

# Skill — GIFI Simulation Engineer

**Autor:** Emerson Antônio  
**Data:** 2026-07-09

## When to Use

- Treinar / comparar Baseline, ElasticNet e RandomForest por elo
- Executar cascata Elo 1 → 2 → 3 (Elo 1b fora do MVP)
- Separar Modo A (integração) vs Modo B (isolamento)
- Reportar MAE/RMSE/WAPE intermediários por elo
- Empacotar candidatos para o gate da Camada 4

## Instructions

1. Ler o agente canônico: `.cursor/agents/gifi-simulation-engineer.md`
2. KB-first: `docs/kb/ml-tabular/index.md` + `quick-reference.md`
3. Contratos/faixas/holdout: `docs/kb/gifi-domain/` (não inventar limiares)
4. Representação inválida → escalar `gifi-ingest-engineer`
5. Release / Matriz A∧B∧C → escalar `gifi-acceptance-engineer` (não liberar produção aqui)
6. Respeitar holdout temporal Confirmado (treino até 2025-04; holdout 2025-05→2025-10)

## KB Entry Points

| Path | Uso |
|------|-----|
| `docs/kb/ml-tabular/concepts/cascade-regression.md` | Encadeamento dos elos |
| `docs/kb/ml-tabular/concepts/elasticnet-vs-rf.md` | Famílias MVP |
| `docs/kb/ml-tabular/patterns/train-select-champion.md` | Seleção de candidato |
| `docs/kb/ml-tabular/patterns/mode-a-b-inference.md` | Inferência A/B |
| `docs/kb/gifi-domain/concepts/platform-layers.md` | Fronteira Camada 3 |

## Do Not

- Incluir Elo 1b (% Casca) no caminho de release do MVP
- Embaralhar train/test ignorando holdout temporal
- Declarar campeão sem passagem pelo aceite A∧B∧C
- Alterar faixas/MAE normativo sem change request via domain specialist

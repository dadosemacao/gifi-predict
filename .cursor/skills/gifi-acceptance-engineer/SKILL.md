---
name: gifi-acceptance-engineer
description: >
  Gate de confiança GIFI Camada 4 (Matrizes A/B/C, MAE≤56, campeão, release).
  Use when deciding production bind, running acceptance matrices, or blocking
  UI release with incomplete A∧B∧C evidence.
---

# Skill — GIFI Acceptance Engineer

**Autor:** Emerson Antônio  
**Data:** 2026-07-09

## When to Use

- Executar / auditar Matriz A (holdout, MAE≤56, RMSE/WAPE)
- Executar Matriz B (monotonicidade / estresse físico, TC+TM)
- Executar Matriz C (top-3 detratores ΔTSA)
- Aplicar política de campeão (só libera se A ∧ B ∧ C)
- Distinguir UI modo demonstração vs release produtivo

## Instructions

1. Ler o agente canônico: `.cursor/agents/gifi-acceptance-engineer.md`
2. KB-first: `docs/kb/gifi-domain/concepts/acceptance-matrices.md` + `patterns/champion-policy.md`
3. Métricas/física: `docs/kb/ml-tabular/concepts/stage-metrics.md` + `physics-constraints.md`
4. A+B parcial habilita só testes internos — nunca produção
5. Falha de candidatos → escalar `gifi-simulation-engineer`
6. Mudança de limiar Confirmado → `gifi-domain-specialist` (change request)

## KB Entry Points

| Path | Uso |
|------|-----|
| `docs/kb/gifi-domain/concepts/acceptance-matrices.md` | Protocolo A/B/C |
| `docs/kb/gifi-domain/patterns/champion-policy.md` | Gate de release |
| `docs/kb/ml-tabular/concepts/temporal-holdout.md` | Janela D-A |
| `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | TCs oficiais |

## Do Not

- Liberar produção sem Matriz C
- Relaxar MAE≤56 sem change request
- Tratar UI homologação como evidência de aceite estatístico/físico

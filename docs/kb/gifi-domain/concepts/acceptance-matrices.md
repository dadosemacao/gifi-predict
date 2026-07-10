# Acceptance Matrices A/B/C

> **Purpose**: Gate de release — Matrizes A∧B∧C não são intercambiáveis  
> **Confidence**: 0.95  
> **MCP Validated**: 2026-07-09  
> **Autor**: Emerson Antônio · **Fonte**: PRD §4.3; analytical-backbone §4–5

## Overview

Camada 4 libera artefato só se **A ∧ B ∧ C**.  
`A+B parcial` habilita testes internos, nunca uso operacional.

## The Concept

### Matriz A — Estatística

| KPI | Contrato |
|-----|----------|
| MAE holdout | **≤ 56 TSA/dia** |
| Janela | Holdout **2025-05 → 2025-10**; treino até **2025-04** |
| Auxiliares | RMSE e WAPE no relatório |
| Por elo | `MAE_Extrativos`, `MAE_Carga`, `MAE_TSA` (obrigatórios no relatório) |

### Matriz B — Física

| Estímulo (ceteris paribus) | Resposta |
|----------------------------|----------|
| DB_LAB ↓ | TSA ↓ (ou não sobe) |
| VMI ↓ | TSA ↓ |
| Extrativo_AT ↑ | TSA ↓ |
| TPC < 45 (e ↓) | TSA ↓ |
| Carga ↑ | TSA ↓ |
| Mix diluidor ↑ pct_ABC | TSA ↑ vs base |

### Matriz C — Explicabilidade

| Entregável | Critério |
|------------|----------|
| Por cenário | Top-3 detratores com ΔTSA |
| Mínimos | TPC verde, Extrativo_AT, Carga; Casca se feature ativa |
| Método | Importância / SHAP / decomposição documentada |

## Quick Reference

| Símbolo | Significado |
|---------|-------------|
| A | Holdout MAE ≤ 56 |
| B | Monotonicidade / estresse |
| C | Top-3 detratores |
| Gate | `release_ok = A and B and C` |

## Common Mistakes

### Wrong

Aceitar “MAE próximo a 56” ou liberar UI com só Matriz A.

### Correct

Contrato rígido `MAE ≤ 56` + B + C antes do release produtivo.

## Related

- [platform-layers.md](platform-layers.md)
- [closed-decisions.md](closed-decisions.md)
- [../patterns/champion-policy.md](../patterns/champion-policy.md)

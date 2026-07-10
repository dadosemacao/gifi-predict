# GIFI Domain Quick Reference

> Lookup normativo. Detalhes nos concepts/specs.

**Autor:** Emerson Antônio · **Data:** 2026-07-09 · **MCP Validated:** 2026-07-09

## Camadas 1–5

| # | Nome | Critério pronto |
|---|------|-----------------|
| 1 | Domínio | Brief + faixas + TCs + template |
| 2 | Dados | Schema; mix=1; k=0,985 |
| 3 | Motor | Modo A/B; MAE por elo; EN/RF |
| 4 | Aceite | MAE≤56 **e** B **e** C |
| 5 | UI | Upload + curvas + top-3 |

## Limpeza / faixas

| Regra | Valor |
|-------|-------|
| Filtro treino | TSA < 1000 excluir |
| Unidade DB | kg/m³ |
| Imputação Lab | `0.985 * DB_SGF` |
| Mix | soma = 1.0 ± 0.02 |
| Extrativo ótima | 1,5–2,1% |
| TPC verde | < 45 dias |

## Aceite e decisões

| Tema | Contrato |
|------|----------|
| MAE | ≤ 56 TSA/dia |
| Holdout | 2025-05-01 .. 2025-10-30 |
| Treino | ≤ 2025-04-30 |
| Elo 1b | NO-GO MVP |
| Gate | A ∧ B ∧ C |
| Campeão | melhor MAE se A∧B∧C; empate → interpretável |
| Relatório | aderência + desvios assistidos (Marco 4) |
| Matriz C | top-3 ΔTSA; método SHAP/coef/permutation |

## Modos / template

| Modo | Extrativo/Carga |
|------|-----------------|
| A | estimados (proibido injetar) |
| B | injeção permitida |
| Template | artefato Camada 1 — `specs/template_cenario_v0.yaml` |

## Pitfalls

| Don't | Do |
|-------|-----|
| g/cm³ ou fator 0.88 | kg/m³ e 0.985 |
| Liberar UI sem A∧B∧C | Demonstração ≠ release |
| Estimar Casca no MVP | Feature medida no Elo 3 |
| Shuffle temporal | Holdout D-A |

## Fontes

| Doc | Path |
|-----|------|
| PRD | `docs/PRD_GIFI_v1.1.md` |
| Backbone | `docs/sketch/analytical-backbone.md` |
| Decisões | `docs/sketch/DECISOES_GIFI.md` |
| Faixas | `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` |

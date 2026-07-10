# ADR-003: Manifesto filesystem vs MLflow para evolução de modelos

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Status:** Aceito

---

## Contexto

O GIFI precisa versionar candidatos da cascata Elo 1→2→3, rastrear métricas de holdout e promover um campeão para produção somente após o gate **A ∧ B ∧ C** (Camada 4).

Alternativas consideradas:

1. **Filesystem + manifesto JSON** (implementado na Camada 3)
2. **MLflow Tracking + Model Registry**
3. **Databricks MLflow / Microsoft Fabric** (cloud)

---

## Decisão

### Marco 1 (MVP — atual)

Usar **manifesto JSON + joblib** em `models/candidates/{run_id}/`, com pointer `current_candidate.json`.

```
models/
  current_candidate.json
  candidates/{run_id}/
    elo1_{family}.joblib
    elo2_{family}.joblib
    elo3_{family}.joblib
    candidate_manifest.json
    metrics_holdout.json
    explainability.json
```

### Marco 2 (condicional)

Adotar **MLflow Tracking only** (backend local `file://`) se:

- Volume de `simulate train` > ~20 runs/semana, ou
- Comparação sistemática de features/hiperparâmetros exigir UI de experimentos

A Camada 4 continua como **autoridade de promoção** (A∧B∧C).

### Marco 3 (condicional)

Avaliar **MLflow Model Registry** ou registry nativo Databricks se houver deploy multi-ambiente formal na Veracel.

---

## Rationale

| Critério | Filesystem | MLflow |
|----------|------------|--------|
| Cascata 3 elos heterogêneos | Natural (3 joblibs) | Requer convenção custom |
| Gate A∧B∧C normativo | Camada 4 custom | Não substitui |
| Linhagem L2 → L3 | Manifesto referencia L2 | Possível via tags |
| Complexidade MVP | Baixa | Média-alta |
| Alinhamento backbone | `ml-tabular/artifact-packaging` | Fora do MVP (backbone) |
| Auditoria Veracel | JSON legível | Exportável |

**YAGNI:** MAE atual (~95) indica gap de modelagem, não de MLOps platform.

---

## Alternativas rejeitadas

1. **MLflow completo no Marco 1** — overhead sem volume de experimentos
2. **Fabric/MLflow cloud no caminho crítico local** — fora do escopo MVP (PRD)
3. **Único modelo end-to-end** — incompatível com cascata e champion por elo

---

## Consequências

- Camada 4 implementa registry semântico GIFI (promoção pós A∧B∧C)
- Histórico de runs pode usar `models/runs_index.jsonl` (append-only) antes de MLflow
- Revisitar ADR quando Marco 2 triggers forem atingidos

---

## Referências

- `.claude/sdd/features/DESIGN_SIMULATION_ENGINE.md` — Decision 1 (rejeita MLflow MVP)
- `docs/kb/ml-tabular/patterns/artifact-packaging.md`
- `docs/sketch/AGENTES_E_KB_BACKBONE.md` — MLflow fora do MVP

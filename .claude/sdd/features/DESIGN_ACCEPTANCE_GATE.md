# DESIGN: Gate de Confiança e Aceite (Camada 4 GIFI)

> Arquitetura técnica para Matrizes A∧B∧C: revalidação estatística, estresse físico TC/TM, top-3 detratores, política de campeão e bind produtivo vs modo demo.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | ACCEPTANCE_GATE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (design-agent) |
| **DEFINE** | [DEFINE_ACCEPTANCE_GATE.md](./DEFINE_ACCEPTANCE_GATE.md) |
| **Status** | Ready for Build |
| **Stack** | Python 3.11+, pandas, scikit-learn, joblib, shap, pydantic v2, PyYAML, typer, pytest |
| **Depends on** | Camada 2 (L2), Camada 3 (`src/simulation/`) shipped |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACCEPTANCE GATE (Camada 4)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  models/candidates/{run_id}/ ──► L3 Loader ──► Guard (hash + holdout_eligible)│
│         │                              │                                     │
│         │ metrics_holdout.json         │ joblibs + explainability.json       │
│         ▼                              ▼                                     │
│  ┌── Matriz A ──────────────────────────────────────────────────────────┐   │
│  │ Revalidar MAE holdout D-A (≤56) + MAE por elo (re-run ou trust L3)   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ▼                                                                    │
│  ┌── Matriz B ──────────────────────────────────────────────────────────┐   │
│  │ Cenários TC-01…08 + TM-01…05 (YAML) → infer Modo A/B → check físico  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ▼                                                                    │
│  ┌── Matriz C ──────────────────────────────────────────────────────────┐   │
│  │ TC-09/10 → SHAP (tree) / coef×x (linear) → top-3 ΔTSA por cenário    │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ▼                                                                    │
│  Gate Policy: release_ok = A ∧ B ∧ C                                        │
│         │                                                                    │
│         ├──► reports/acceptance/{run_id}/acceptance_report.json             │
│         ├──► (fail) demo_mode=true, production_bind=false                   │
│         └──► (pass) models/champion/{run_id}/ + current_champion.json       │
│                                                                              │
│  Reutiliza: simulation.cascade.inference, simulation.package.publisher       │
│  Consumers: Camada 5 (bind produtivo vs demo), auditoria stakeholder          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Package path | Purpose | Maps to |
|-----------|--------------|---------|---------|
| **Config** | `src/acceptance/config.py` | `AcceptanceSettings`, paths, MAE limit | — |
| **L3 Loader** | `src/acceptance/l3/loader.py` | Carregar candidato por `run_id` | FR-ACC-01 |
| **L3 Guard** | `src/acceptance/l3/guard.py` | Hash joblib vs manifest; `holdout_eligible` L2 | FR-ACC-02, FR-ACC-13 |
| **Matriz A** | `src/acceptance/matrices/matriz_a.py` | MAE holdout + por elo | FR-ACC-03, FR-ACC-04 |
| **Matriz B** | `src/acceptance/matrices/matriz_b.py` | TC + TM via inferência | FR-ACC-05…07 |
| **Matriz C** | `src/acceptance/matrices/matriz_c.py` | Top-3 detratores | FR-ACC-08, FR-ACC-09 |
| **Scenarios** | `src/acceptance/scenarios/` | YAML → `DataFrame` inferível | Cenários versionados |
| **Inference Runner** | `src/acceptance/runner/inference.py` | Wrapper Modo A/B sobre L3 | FR-ACC-07 |
| **Gate Policy** | `src/acceptance/policy/gate.py` | `A ∧ B ∧ C`, demo vs prod | FR-ACC-14 |
| **Champion Publisher** | `src/acceptance/package/champion.py` | Cópia imutável + pointer | FR-ACC-11 |
| **Reporter** | `src/acceptance/package/reporter.py` | JSON + summary MD | FR-ACC-12 |
| **Pipelines** | `src/acceptance/pipeline/` | `accept`, `report` | Orquestração |
| **Observability** | `src/acceptance/observability/` | Logs JSON `accept_*` | NFR-ACC-03 |
| **CLI** | `src/acceptance/cli.py` | `accept run`, `accept report` | SHOULD |

---

## Key Decisions

### Decision 1: Layout físico L4 (reports + champion)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** Candidatos L3 permanecem imutáveis; aceite gera evidência auditável separada do treino.

**Choice:**

```text
reports/acceptance/{run_id}/
  acceptance_report.json       # gate consolidado A∧B∧C
  matriz_a.json
  matriz_b_results.json        # TC/TM pass/fail detalhado
  matriz_c_detractors.json     # top-3 por cenário TC-09/10
  acceptance_summary.md        # human-readable para homologação

models/champion/{run_id}/      # cópia imutável (só se release_ok)
  elo1_{family}.joblib
  elo2_{family}.joblib
  elo3_{family}.joblib
  champion_manifest.json       # refs L2 + L3 + gate report hash
  acceptance_report.json       # snapshot do report

models/current_champion.json   # pointer produtivo (só se A∧B∧C)
models/current_champion.json.previous
```

**Rationale:** Espelha padrão L2/L3 (imutável + pointer); UI lê `current_champion.json` para bind produtivo.

**Alternatives Rejected:**
1. Report dentro de `models/candidates/` — mistura treino e aceite
2. Sobrescrever candidato L3 — perde rastreio de submissões

**Consequences:**
- `reports/` e `models/champion/` no `.gitignore`
- Gate fail não toca `current_champion.json`

---

### Decision 2: Reutilizar API Python da Camada 3 (sem subprocess)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE SHOULD reutilizar inferência L3; duplicar cascata viola DRY e diverge Modo A/B.

**Choice:** Importar diretamente:

- `simulation.package.publisher.load_candidate_pipes_by_run_id`
- `simulation.cascade.inference.infer_dataframe` / `infer_cascade_row`
- `simulation.cascade.evaluator.evaluate_holdout` (Matriz A recompute)
- `simulation.l2.loader.load_l2_bundle` + guards

**Rationale:** Monorepo `gifi-predict`; smoke E2E ingest→infer já validado; `--run-id` desbloqueia demo sem `current_candidate.json`.

**Alternatives Rejected:**
1. `subprocess simulate infer` — frágil, parsing stdout, paths
2. Reimplementar cascata em `acceptance/` — risco de drift Modo A/B

**Consequences:**
- `acceptance` depende de pacote `simulation` (mesmo wheel)
- Testes usam fixtures mini L2 + candidato sintético

---

### Decision 3: Matriz A — recompute holdout com opção trust-L3

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** L3 já grava `metrics_holdout.json`; gate deve ser autoritativo mas evitar re-treino.

**Choice:**

| Modo | Comportamento |
|------|---------------|
| **Default (`recompute_matriz_a: true`)** | Re-executa `evaluate_holdout` com joblibs L3 + holdout L2 atual |
| **Fast path (`recompute_matriz_a: false`)** | Lê `metrics_holdout.json`; sanity check campos obrigatórios |

Ambos aplicam limiar rígido `mae_tsa_cascade ≤ 56.0` (sem tolerância).

**Rationale:** Detecta drift L2 pós-treino; fast path útil em CI repetido.

**Consequences:**
- Report inclui `matriz_a.source`: `"recomputed"` | `"l3_metrics"`

---

### Decision 4: Cenários TC/TM em YAML (`config/acceptance_scenarios/`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #2 — KB vs config.

**Choice:** YAML executável em `config/acceptance_scenarios/` com campo `normative_ref` apontando para `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` e KB.

**Schema mínimo por cenário:**

```yaml
id: TC-05
mode: B
description: "TPC verde — penalização rendimento"
inputs:
  pct_A: 0.2
  pct_B: 0.2
  pct_C: 0.2
  pct_D: 0.2
  pct_MG: 0.2
  TPC: 30
  Volume: 8600
  DB_SGF: 483
  Kappa: 17.0
  Idade: 8
  Extrativo_AT: 2.0
  Carga_Alcalina: 19.5
expect:
  type: compare_baseline
  baseline_id: TC-05-baseline-tpc65
  direction: down          # TSA(stressed) < TSA(baseline)
```

**TM monotonicidade:**

```yaml
id: TM-01
mode: A
anchor: anchor_mixed
variable: DB_LAB
sequence: [520, 490, 460, 440]
expect: non_up             # TSA não aumenta ao longo da sequência
```

**Rationale:** Reproduzível, versionável, editável sem redeploy; KB permanece normativa.

**Consequences:**
- Loader calcula features derivadas (`pct_ABC`, `mix_entropy`, etc.) via função compartilhada ou reusa colunas já presentes no anchor
- Cenários Modo B injetam Extrativo/Carga conforme template

---

### Decision 5: Matriz B — avaliação por direção física, não faixa absoluta

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** TC-01/02 esperam patamares históricos (~3400 TSA) que o modelo atual não atinge (MAE gap); gate B não deve falhar por escala errada se direção estiver correta.

**Choice:**

| Tipo expect | Regra |
|-------------|-------|
| `direction: down` | `stressed < baseline` |
| `direction: up` | `stressed > baseline` |
| `direction: non_up` | `stressed <= baseline` (TM-01 DB) |
| `monotonic_sequence` | TSA não viola direção ao longo de `sequence` |
| `threshold` (opcional) | Só para TCs com limiar explícito no brief (ex.: Carga > 21%) |

**Rationale:** Alinha `physics-constraints.md`; separa acurácia (Matriz A) de plausibilidade direcional (Matriz B).

**Alternatives Rejected:**
1. Assert TSA ≈ 3430 em TC-01 — bloqueia gate enquanto MAE > 56 sem informação útil

**Consequences:**
- `matriz_b_results.json` registra `baseline_tsa`, `stressed_tsa`, `delta`, `pass`

---

### Decision 6: Matriz C — SHAP tree / coef linear / permutation fallback

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open #1; campeão atual pode ser CatBoost/XGB/LGBM/RF/EN.

**Choice:**

| Família elo3 | Método | Implementação |
|--------------|--------|---------------|
| `elasticnet`, `ridge`, `lasso` | Decomposição linear | `coef_i × x_i` |
| `randomforest`, `extratrees`, `xgboost`, `lightgbm`, `catboost` | SHAP local | `shap.TreeExplainer` |
| `histgradientboosting`, `baseline` | Fallback | `permutation_importance` global no holdout (documentado) |

Top-3 = maiores `|delta_tsa|` por cenário TC-09 e TC-10.

**Aceite cenário (TC-09/10):**

- TC-09: `TPC` ∈ top-3 features
- TC-10: `Extrativo_AT` ou `Carga_Alcalina` ∈ top-3

**Rationale:** KB `matriz-c-detractors.md`; L3 `explainability.json` é global, Matriz C é **local por cenário**.

**Consequences:**
- Nova dependência: `shap>=0.44` em `pyproject.toml`
- Report inclui `method` por detractor

---

### Decision 7: Gate e política demo vs produção

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:**

```python
release_ok = matriz_a.ok and matriz_b.ok and matriz_c.ok
production_bind = release_ok
demo_mode = not release_ok  # UI pode operar com run_id explícito
```

| Estado | `current_champion.json` | `current_candidate.json` (L3) |
|--------|-------------------------|----------------------------------|
| Gate pass | Atualizado | Inalterado (L3 pointer opcional) |
| Gate fail | Preservado (last-good) | Inalterado |

**Rationale:** `analytical-backbone.md` §4 — UI demo até 31/08 sem bind produtivo.

---

### Decision 8: Integridade L3 antes de executar matrizes

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** Reutilizar SHA256 do `candidate_manifest.json`; recalcular hash de cada joblib antes de load. Mismatch → `IntegrityError` (AT-ACC-012).

**Choice:** Bloquear se L2 `holdout_eligible=false` (AT-ACC-011).

---

### Decision 9: Champion = run_id explícito do `accept run` (Marco 1)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open #3 — comparador multi-run.

**Choice:** `accept run --run-id <id>` avalia **um** candidato. Seleção entre múltiplos runs elegíveis = SHOULD Marco 2.

**Rationale:** Evita ambiguidade; CD submete candidato conscientemente.

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `pyproject.toml` | Modify | `accept` script, `shap` dep, `acceptance` coverage | python-developer | — |
| 2 | `config/acceptance.yaml` | Create | MAE limit, paths, flags recompute | gifi-acceptance-engineer | — |
| 3 | `config/acceptance_scenarios/anchor_mixed.yaml` | Create | Cenário âncora TM | gifi-domain-specialist | — |
| 4 | `config/acceptance_scenarios/tc01..tc08.yaml` | Create | Matriz B TCs | gifi-domain-specialist | 3 |
| 5 | `config/acceptance_scenarios/tm01..tm05.yaml` | Create | Monotonicidades | gifi-domain-specialist | 3 |
| 6 | `config/acceptance_scenarios/tc09_tpc.yaml` | Create | Matriz C TC-09 | gifi-domain-specialist | 5 |
| 7 | `config/acceptance_scenarios/tc10_stress.yaml` | Create | Matriz C TC-10 | gifi-domain-specialist | — |
| 8 | `src/acceptance/__init__.py` | Create | Package root | python-developer | — |
| 9 | `src/acceptance/config.py` | Create | Settings pydantic | python-developer | 2 |
| 10 | `src/acceptance/exceptions.py` | Create | IntegrityError, GateError | python-developer | — |
| 11 | `src/acceptance/l3/loader.py` | Create | Load candidate + manifest | gifi-acceptance-engineer | simulation |
| 12 | `src/acceptance/l3/guard.py` | Create | Hash + holdout guard | gifi-acceptance-engineer | 11 |
| 13 | `src/acceptance/scenarios/loader.py` | Create | Load YAML scenarios | gifi-acceptance-engineer | 3–7 |
| 14 | `src/acceptance/scenarios/features.py` | Create | Derivar pct_ABC, entropy, dom_* | gifi-ingest-engineer | 13 |
| 15 | `src/acceptance/runner/inference.py` | Create | Modo A/B wrapper | gifi-simulation-engineer | simulation |
| 16 | `src/acceptance/matrices/matriz_a.py` | Create | MAE gate | gifi-acceptance-engineer | 11, 15 |
| 17 | `src/acceptance/matrices/matriz_b.py` | Create | TC/TM runner | gifi-acceptance-engineer | 13, 15 |
| 18 | `src/acceptance/matrices/matriz_c.py` | Create | Top-3 detratores | gifi-acceptance-engineer | 15, shap |
| 19 | `src/acceptance/policy/gate.py` | Create | A∧B∧C combiner | gifi-acceptance-engineer | 16–18 |
| 20 | `src/acceptance/package/reporter.py` | Create | JSON + MD | gifi-acceptance-engineer | 19 |
| 21 | `src/acceptance/package/champion.py` | Create | Promote champion | gifi-acceptance-engineer | 20 |
| 22 | `src/acceptance/package/atomic_io.py` | Create | Reuse pattern L3 | python-developer | — |
| 23 | `src/acceptance/pipeline/accept.py` | Create | Orquestração principal | gifi-acceptance-engineer | 11–21 |
| 24 | `src/acceptance/pipeline/report.py` | Create | `accept report` read-only | gifi-acceptance-engineer | 20 |
| 25 | `src/acceptance/observability/logging.py` | Create | JSON logs | python-developer | — |
| 26 | `src/acceptance/cli.py` | Create | Typer CLI | python-developer | 23–24 |
| 27 | `tests/acceptance/conftest.py` | Create | Fixtures mini L3 + scenarios | test-generator | simulation tests |
| 28 | `tests/acceptance/test_matriz_a.py` | Create | AT-ACC-002/003 | test-generator | 16 |
| 29 | `tests/acceptance/test_matriz_b.py` | Create | AT-ACC-004/005 | test-generator | 17 |
| 30 | `tests/acceptance/test_matriz_c.py` | Create | AT-ACC-006/007 | test-generator | 18 |
| 31 | `tests/acceptance/test_gate_policy.py` | Create | AT-ACC-008/009/010/013 | test-generator | 19–21 |
| 32 | `tests/acceptance/test_accept_pipeline.py` | Create | AT-ACC-001/015 integration | test-generator | 23 |
| 33 | `tests/acceptance/test_integration_excel.py` | Create | AT-ACC-003/014 `@slow` | test-generator | 23 |
| 34 | `.gitignore` | Modify | `reports/acceptance/`, `models/champion/` | python-developer | — |

**Total Files:** 34

---

## Agent Assignment Rationale

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| **gifi-acceptance-engineer** | 2, 11–21, 23–24 | Dono Matrizes A/B/C e gate |
| **gifi-domain-specialist** | 3–7 | TC/TM normativos do brief |
| **gifi-simulation-engineer** | 15 | Integração inferência L3 |
| **gifi-ingest-engineer** | 14 | Features derivadas alinhadas L2 |
| **python-developer** | 1, 8–10, 22, 25–26 | Layout, CLI, IO |
| **test-generator** | 27–33 | Cobertura AT-ACC |

---

## Code Patterns

### Pattern 1: Gate combiner

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    matriz_a: bool
    matriz_b: bool
    matriz_c: bool

    @property
    def release_ok(self) -> bool:
        return self.matriz_a and self.matriz_b and self.matriz_c

    @property
    def production_bind(self) -> bool:
        return self.release_ok

    @property
    def demo_mode(self) -> bool:
        return not self.release_ok
```

### Pattern 2: Matriz B monotonic check

```python
def check_monotonic_sequence(tsa_values: list[float], expect: str) -> bool:
    if expect == "non_up":
        return all(tsa_values[i] >= tsa_values[i + 1] for i in range(len(tsa_values) - 1))
    if expect == "down":
        return all(tsa_values[i] > tsa_values[i + 1] for i in range(len(tsa_values) - 1))
    raise ValueError(f"unknown expect: {expect}")
```

### Pattern 3: Matriz C detractor selection

```python
from simulation.models.families import make_family  # noqa: F401 — exemplo


def top3_detractors(model, family: str, x_row, feature_names: list[str]):
    if family in {"elasticnet", "ridge", "lasso"}:
        coef = model.coef_.ravel()
        x = x_row.to_numpy(dtype=float).ravel()
        pairs = sorted(
            zip(feature_names, coef * x, strict=True),
            key=lambda p: abs(p[1]),
            reverse=True,
        )
        return [{"feature": f, "delta_tsa": float(v), "method": "coef"} for f, v in pairs[:3]]

    import shap

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(x_row)
    values = sv[0] if isinstance(sv, list) else sv
    pairs = sorted(
        zip(feature_names, values.ravel(), strict=True),
        key=lambda p: abs(p[1]),
        reverse=True,
    )
    return [{"feature": f, "delta_tsa": float(v), "method": "shap"} for f, v in pairs[:3]]
```

### Pattern 4: Pipeline accept (orquestração)

```python
def run_accept_pipeline(settings, *, run_id: str) -> dict:
    bundle = load_l3_candidate(settings.models_path, run_id)
    guard_l3_integrity(bundle)
    l2 = load_l2_bundle(settings.l2_path)
    guard_holdout_eligible(l2.manifest)

    ma = run_matriz_a(bundle, l2, settings)
    mb = run_matriz_b(bundle, settings)
    mc = run_matriz_c(bundle, settings)
    gate = combine_gate(ma, mb, mc)

    report = build_acceptance_report(run_id, bundle, l2, ma, mb, mc, gate)
    publish_report(settings.reports_path, run_id, report)

    if gate.release_ok:
        promote_champion(settings.models_path, run_id, report)

    return {"run_id": run_id, "release_ok": gate.release_ok, "report": str(report_path)}
```

### Pattern 5: Configuration (`config/acceptance.yaml`)

```yaml
# Autor: Emerson Antônio | Data: 2026-07-10
repo_root: "."
l2_root: "data/l2"
models_root: "models"
reports_root: "reports/acceptance"
logs_root: "logs/acceptance"
scenarios_dir: "config/acceptance_scenarios"
mae_limit: 56.0
recompute_matriz_a: true
holdout:
  start: "2025-05-01"
  end: "2025-10-30"
matriz_c:
  required_in_top3:
    TC-09: [TPC]
    TC-10: [Extrativo_AT, Carga_Alcalina]
io:
  lock_timeout_s: 30
  max_retries: 3
```

---

## Data Flow

```text
1. accept run --run-id <l3_run_id>
   │
   ├─► load_candidate_pipes_by_run_id + candidate_manifest
   ├─► guard: sha256 joblibs, holdout_eligible L2
   ├─► Matriz A: evaluate_holdout → mae_tsa_cascade vs 56
   ├─► Matriz B: for each TC/TM YAML → infer → direction check
   ├─► Matriz C: TC-09/10 → SHAP/coef → top-3 + coverage check
   ├─► gate = A ∧ B ∧ C
   ├─► write reports/acceptance/{run_id}/*
   └─► if release_ok: copy → models/champion/{run_id}/ + current_champion.json

2. accept report --run-id <id>
   │
   └─► read acceptance_report.json + echo summary (no re-run)
```

---

## Integration Points

| System | Type | Contract |
|--------|------|----------|
| Camada 2 L2 | Filesystem | `current.json`, holdout Parquet, `holdout_eligible` |
| Camada 3 L3 | Filesystem + import | `models/candidates/{run_id}/`, inference API |
| Camada 5 UI | Filesystem | `current_champion.json`, `acceptance_report.json`, `demo_mode` flag |
| KB TC/TM | Read-only YAML refs | `CASOS_TESTE`, `acceptance-matrices.md` |
| SHAP | Python lib | TreeExplainer para famílias tree/boosting |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | ATs |
|-----------|-------|-------|-------|-----|
| Unit | Matriz A/B/C isoladas | `test_matriz_*.py` | pytest | AT-ACC-002…007 |
| Unit | Gate policy | `test_gate_policy.py` | pytest | AT-ACC-008…010, 013 |
| Integration | Pipeline mini | `test_accept_pipeline.py` | pytest + l2_mini + candidato sintético | AT-ACC-001, 015 |
| Integration | Excel real | `test_integration_excel.py` `@slow` | pytest | AT-ACC-003, 014 |
| Smoke manual | Ingest→L3→L4 | README | CLI | E2E homologação |

**Fixture strategy:**

- Reutilizar `tests/simulation/fixtures/l2_mini/`
- Novo `tests/acceptance/fixtures/l3_mini/` — candidato treinado com DummyRegressor (MAE sintético ≤56 para happy path)
- Cenários TC reduzidos em `tests/acceptance/fixtures/scenarios/` para TM/TC unitários

**Happy path sintético (AT-ACC-009):** Dummy pipelines com monotonicidade forçada → gate pass → champion criado.

**Excel smoke (AT-ACC-003):** run_id real → `matriz_a=false`, `release_ok=false`, report completo, champion intacto.

---

## Error Handling

| Error / Signal | Handling | Retry? |
|----------------|----------|--------|
| Candidato não encontrado | Fail fast `FileNotFoundError` | Não |
| Hash joblib mismatch | `IntegrityError`; sem report final | Não |
| `holdout_eligible=false` | Bloqueia gate (AT-ACC-011) | Não |
| Cenário YAML inválido | Fail com `scenario_id` + campo | Não |
| SHAP indisponível para família | Fallback permutation + warning no report | Não |
| Gate fail parcial | Report completo com flags; last-good champion | Re-run após fix L3 |
| Lock timeout champion | `TimeoutError` | Retry manual |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `mae_limit` | float | 56.0 | Limiar Matriz A |
| `recompute_matriz_a` | bool | true | Re-run evaluate vs trust L3 metrics |
| `scenarios_dir` | path | `config/acceptance_scenarios` | TC/TM YAML |
| `reports_root` | path | `reports/acceptance` | Saída auditável |
| `l2_root` | path | `data/l2` | Holdout + cenários publicados |
| `models_root` | path | `models` | Candidatos + champion |

---

## Security Considerations

- Joblib load exclusivamente via paths resolvidos sob `models_root` (reutilizar guard L3)
- Reports não executam código dos YAML (somente dados tipados)
- Champion copy verifica SHA256 antes de promote

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | JSON lines `logs/acceptance/accept_{run_id}.jsonl` |
| Events | `accept_start`, `matriz_a_done`, `matriz_b_done`, `matriz_c_done`, `accept_end` |
| Metrics in report | Duração por matriz, contagem TC pass/fail |

---

## Success Criteria Verification (Build targets)

| Criterion | Target | Verification |
|-----------|--------|--------------|
| AT-ACC-001 | Report A/B/C flags | `test_accept_pipeline` |
| AT-ACC-003 | Excel MAE fail | `test_integration_excel` @slow |
| AT-ACC-009 | Champion promoted | `test_gate_policy` happy path |
| AT-ACC-010 | Last-good preserved | `test_gate_policy` fail after pass |
| AT-ACC-015 | Determinismo | double `accept run` assert JSON equal |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | design-agent | DESIGN inicial Camada 4 |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_ACCEPTANCE_GATE.md`

**Agentes no Build:**

- **Owner:** `gifi-acceptance-engineer`
- **Normativo:** `gifi-domain-specialist` (validar YAML TC/TM)
- **Integração:** `gifi-simulation-engineer`
- **Testes:** `test-generator`

# DESIGN: Motor de Simulação (Camada 3 GIFI)

> Arquitetura técnica para cascata Elo 1→2→3: carga L2, treino Baseline/EN/RF, inferência Modo A/B, métricas holdout e empacotamento de candidatos para Camada 4.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SIMULATION_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (design-agent) |
| **DEFINE** | [DEFINE_SIMULATION_ENGINE.md](./DEFINE_SIMULATION_ENGINE.md) |
| **Status** | Shipped |
| **Stack** | Python 3.11+, pandas, pyarrow, scikit-learn, joblib, pydantic v2, PyYAML, typer, pytest |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SIMULATION ENGINE (Camada 3)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  data/l2/current.json ──► L2 Loader ──► Guard (schema + holdout_eligible)   │
│         │                         │                                          │
│         │ train_features          │ holdout_features                         │
│         ▼                         ▼                                          │
│  ┌── Feature Matrix (por elo) ──────────────────────────────────────────┐   │
│  │ E1: mix+Idade → Extrativo_AT                                          │   │
│  │ E2: Extrativo_AT+TPC+DB_SGF → Carga_Alcalina   (teacher forcing fit)  │   │
│  │ E3: mix+qualidade+processo → TSA_dia             (teacher forcing fit)  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ▼                                                                    │
│  ┌── Trainer (×3 famílias × 3 elos) ──► Selector (champion por elo) ──┐   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         ├──► Evaluator (holdout D-A, MAE/RMSE/WAPE)                         │
│         ├──► Packager → models/candidates/{run_id}/                         │
│         └──► Inferencer (Modo A/B) ← infer_features / cenário               │
│                                                                              │
│  KB (read-only): docs/kb/ml-tabular/ · docs/kb/gifi-domain/                 │
│  Consumers: Camada 4 (Matrizes A/B/C) · Camada 5 (curvas via API local)     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Package path | Purpose | Maps to |
|-----------|--------------|---------|---------|
| **Config** | `src/simulation/config.py` | `SimulationSettings`, paths L2/L3 | — |
| **L2 Loader** | `src/simulation/l2/` | Resolver `current.json`, ler Parquet+manifest | FR-SIM-01 |
| **L2 Guard** | `src/simulation/l2/guard.py` | `schema_version` major, `holdout_eligible` | FR-SIM-02, FR-SIM-12 |
| **Features** | `src/simulation/features/` | Matrizes X/y por elo; sparse `Casca_pct` | FR-SIM-03..05, FR-SIM-13 |
| **Metrics** | `src/simulation/metrics/` | MAE, RMSE, WAPE | FR-SIM-07 |
| **Models** | `src/simulation/models/` | Famílias sklearn, treino, seleção | FR-SIM-08 |
| **Cascade** | `src/simulation/cascade/` | Inferência Modo A/B, avaliação holdout | FR-SIM-09, FR-SIM-10 |
| **Package** | `src/simulation/package/` | Manifesto L3, joblib atômico | FR-SIM-11 |
| **Pipelines** | `src/simulation/pipeline/` | `train`, `evaluate`, `infer` | Orquestração |
| **Observability** | `src/simulation/observability/` | Logs JSON `simulate_*` | NFR-SIM-04 |
| **CLI** | `src/simulation/cli.py` | `simulate train|evaluate|infer` | SHOULD |

---

## Key Decisions

### Decision 1: Layout físico L3 (`models/`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** Candidatos L3 precisam de versionamento imutável e pointer last-good, espelhando L2.

**Choice:**

```text
models/
  current_candidate.json          # pointer: run_id + paths + l2_dataset_version
  candidates/{run_id}/
    elo1_{family}.joblib          # sklearn Pipeline
    elo2_{family}.joblib
    elo3_{family}.joblib
    candidate_manifest.json       # refs L2, famílias por elo, seed, timestamps
    metrics_holdout.json          # MAE/RMSE/WAPE por elo + cascade TSA
    explainability.json           # coefs EN / importances RF (básico L3)
  .staging_{run_id}/              # escrita atômica; removido após promote
```

**Rationale:** `run_id` = ISO UTC (`2026-07-10T08:00:00Z`); imutável após package; Camada 4 lê manifesto sem re-treinar.

**Alternatives Rejected:**
1. Único `models/latest/` — perde auditoria de candidatos
2. MLflow no MVP — YAGNI local-first

**Consequences:**
- `models/` no `.gitignore`
- `current_candidate.json` só atualiza se package completo e sem erro estrutural

---

### Decision 2: Champion por elo (famílias heterogêneas)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE open question #2 — champion único vs por elo.

**Choice:** Selecionar **melhor família independentemente por elo** (MAE holdout isolado daquele estágio). Manifesto registra `elo1_family`, `elo2_family`, `elo3_family` (podem diferir, ex.: EN+EN+RF).

**Rationale:** Maximiza skill por estágio; alinha `train-select-champion.md` e diagnóstico Mode B.

**Alternatives Rejected:**
1. Champion único (mesma família nos 3 elos) — rejeitado: força subótimo em elos com perfis diferentes
2. Grid conjunto end-to-end — rejeitado: custo 3³ combinações sem ganho MVP

**Consequences:**
- Inferência sempre monta cascata com 3 joblibs possivelmente distintos
- Manifesto L3 lista hash de cada arquivo

---

### Decision 3: Teacher forcing no treino; Mode A na avaliação TSA

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** Cascata supervisionada — risco de error compounding no fit vs avaliação realista.

**Choice:**

| Fase | Elo 2 X | Elo 3 X | Métrica |
|------|---------|---------|---------|
| **Fit (train)** | `Extrativo_AT` **real** | `Extrativo_AT`, `Carga_Alcalina` **reais** | Teacher forcing |
| **Holdout per-elo** | `Extrativo_AT` **real** | intermediários **reais** | `MAE_Extrativos`, `MAE_Carga`, `MAE_Elo3_isolated` |
| **Holdout Matriz A** | pred E1 | pred E1 → pred E2 | `MAE_TSA_cascade` (gate ≤56) |

**Rationale:** Fit estável; KPI global reflete compounding Mode A (TC-A01).

**Alternatives Rejected:**
1. Sempre preditos no fit — instável com poucos dados
2. Só MAE isolado Elo 3 — ignora compounding que a UI Modo A sofre

**Consequences:**
- `metrics_holdout.json` distingue `mae_tsa_cascade` (gate) vs `mae_tsa_isolated` (diagnóstico)

---

### Decision 4: Reutilizar contrato L2 sem re-split

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** L3 **não** re-particiona dados. Confia em `train_features` / `holdout_features` do Ingest. Valida janela holdout por assert em `data_processo` (sanity check AT-002).

**Rationale:** D-A é decisão fechada; única fonte de verdade L2.

**Consequences:**
- Se ingest errar split, L3 falha sanity → escalar ingest-engineer

---

### Decision 5: `SchemaVersionError` compartilhado com Ingest

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** `from ingest.contracts.models import SchemaVersionError` — comparar major de `batch_manifest.schema_version` vs `config/simulation.yaml`.

**Rationale:** Mesma exceção semântica; pacote monorepo `gifi-ingest` já instalado.

---

### Decision 6: Explicabilidade básica em L3 (SHAP na Camada 4)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** Exportar `explainability.json` com coeficientes ElasticNet (Elo 3) e `feature_importances_` RF. Top-3 detratores (Matriz C) ficam na Camada 4.

**Rationale:** DEFINE open #3; evita dependência SHAP no Marco 1.

---

### Decision 7: Publicação atômica de candidatos (com lock e rollback)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:**

1. Escrever em `models/candidates/.staging_{run_id}/`
2. `fcntl` lock em `models/.train.lock` durante package + update pointer (espelha ingest `atomic_io.file_lock`)
3. `os.replace(staging, final)` só após manifesto + 3 joblibs + métricas completos
4. `current_candidate.json` atualizado via `atomic_write_json` + backup `current_candidate.json.previous`
5. Em falha: `shutil.rmtree(staging)`; **não** tocar `current_candidate.json`
6. I/O com retry 3× backoff 100–500ms (read Parquet L2, write joblib)

**Rationale:** Judge advisory — race em pointer; rollback explícito; transient FS errors.

**Alternatives Rejected:**
1. Pointer sem lock — risco em train paralelo acidental
2. Escrita direta em `candidates/{run_id}/` — corrupção mid-write

**Consequences:**
- `src/simulation/package/atomic_io.py` (reuso de padrão ingest, sem import cruzado obrigatório)
- Marco 2: lock distribuído se multi-host

---

### Decision 8: Limpeza de feature matrix (NaN / missing)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** `build_matrix(elo, df)` aplica regras determinísticas:

| Regra | Ação |
|-------|------|
| `y` NaN | Excluir linha; contar em `exclusions.elo{n}_na_target` |
| Feature obrigatória NaN | Excluir linha; contar em `exclusions.elo{n}_na_feature` |
| Feature opcional (`Casca_pct`) ausente na coluna | Omitir do X; não falhar |
| Feature opcional presente com NaN | Imputar mediana do **train** (fit transformer); persistir no pipeline sklearn quando aplicável |
| Inf / dtype inválido | `pd.to_numeric(..., errors="coerce")` → tratar como NaN |

Mínimo de linhas após limpeza: **50** no train por elo; senão `TrainingDataError`.

**Rationale:** Judge advisory — null handling; evita `fit()` sklearn com NaN silencioso.

**Consequences:**
- Manifesto L3 inclui bloco `exclusions` por elo
- Holdout usa mesmos transformers fitados no train (sem leakage)

---

### Decision 9: Joblib load seguro (path allowlist)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** `load_pipeline(path)` só aceita paths cuja resolução `Path.resolve()` está **sob** `models_root.resolve()`. Rejeitar symlinks externos e paths absolutos fora do repo. Nunca `joblib.load()` em paths de upload do usuário.

**Rationale:** Judge advisory — deserialização insegura.

**Consequences:**
- Inferência carrega apenas de `current_candidate.json` paths validados

## File Manifest

| # | File | Action | Purpose | Agent | Deps |
|---|------|--------|---------|-------|------|
| 1 | `pyproject.toml` | Modify | deps sklearn/joblib; script `simulate` | python-developer | — |
| 2 | `config/simulation.yaml` | Create | schema, seed, families, paths | gifi-simulation-engineer | — |
| 3 | `src/simulation/__init__.py` | Create | package root | python-developer | — |
| 4 | `src/simulation/config.py` | Create | `SimulationSettings` | python-developer | 2 |
| 5 | `src/simulation/l2/__init__.py` | Create | subpackage | python-developer | — |
| 6 | `src/simulation/l2/loader.py` | Create | `L2Bundle` from `current.json` | gifi-simulation-engineer | 4 |
| 7 | `src/simulation/l2/guard.py` | Create | schema + holdout guards | gifi-simulation-engineer | 6 |
| 8 | `src/simulation/features/__init__.py` | Create | subpackage | python-developer | — |
| 9 | `src/simulation/features/elo_specs.py` | Create | colunas X/y por elo | gifi-domain-specialist | KB |
| 10 | `src/simulation/features/matrix.py` | Create | build matrices, drop NA targets | gifi-simulation-engineer | 9 |
| 11 | `src/simulation/metrics/__init__.py` | Create | subpackage | python-developer | — |
| 12 | `src/simulation/metrics/stage.py` | Create | mae, rmse, wape | gifi-simulation-engineer | — |
| 13 | `src/simulation/models/__init__.py` | Create | subpackage | python-developer | — |
| 14 | `src/simulation/models/families.py` | Create | Baseline, EN, RF pipelines | gifi-simulation-engineer | KB |
| 15 | `src/simulation/models/trainer.py` | Create | fit grid famílias×elos | gifi-simulation-engineer | 10,14 |
| 16 | `src/simulation/models/selector.py` | Create | champion por elo (MAE) | gifi-simulation-engineer | 12,15 |
| 17 | `src/simulation/cascade/__init__.py` | Create | subpackage | python-developer | — |
| 18 | `src/simulation/cascade/inference.py` | Create | Modo A/B `infer_row` | gifi-simulation-engineer | 14 |
| 19 | `src/simulation/cascade/evaluator.py` | Create | holdout metrics + cascade | gifi-simulation-engineer | 12,18 |
| 20 | `src/simulation/package/__init__.py` | Create | subpackage | python-developer | — |
| 21 | `src/simulation/package/manifest.py` | Create | `candidate_manifest.json` | gifi-simulation-engineer | — |
| 22 | `src/simulation/package/atomic_io.py` | Create | lock, atomic JSON, retry I/O | gifi-simulation-engineer | — |
| 23 | `src/simulation/package/publisher.py` | Create | joblib atômico + pointer | gifi-simulation-engineer | 21,22 |
| 24 | `src/simulation/pipeline/__init__.py` | Create | subpackage | python-developer | — |
| 25 | `src/simulation/pipeline/train.py` | Create | orquestra train+package | gifi-simulation-engineer | 6–23 |
| 26 | `src/simulation/pipeline/evaluate.py` | Create | re-score candidato existente | gifi-simulation-engineer | 18,19 |
| 27 | `src/simulation/pipeline/infer.py` | Create | infer `infer_features` | gifi-simulation-engineer | 18 |
| 28 | `src/simulation/observability/logging.py` | Create | JSON logs | gifi-simulation-engineer | — |
| 29 | `src/simulation/cli.py` | Create | typer CLI | python-developer | 25–27 |
| 30 | `.gitignore` | Modify | `models/` | python-developer | — |
| 31 | `tests/simulation/conftest.py` | Create | fixtures L2 mini | test-generator | — |
| 32 | `tests/simulation/fixtures/l2_mini/` | Create | parquet+json sintético | test-generator | — |
| 33 | `tests/simulation/test_l2_guard.py` | Create | AT-004, AT-005 | test-generator | 7 |
| 34 | `tests/simulation/test_metrics.py` | Create | mae/rmse/wape | test-generator | 12 |
| 35 | `tests/simulation/test_matrix_cleaning.py` | Create | NaN exclusions AT | test-generator | 10 |
| 36 | `tests/simulation/test_cascade_inference.py` | Create | AT-006..008 | test-generator | 18 |
| 37 | `tests/simulation/test_train_pipeline.py` | Create | AT-001,003,012,015 | test-generator | 25 |
| 38 | `tests/simulation/test_integration_l2.py` | Create | smoke Excel L2 `@slow` | test-generator | 25 |

**Total Files:** 38

---

## Agent Assignment Rationale

| Agent | Files | Why |
|-------|-------|-----|
| `gifi-simulation-engineer` | 2,6–7,9–10,12–19,21–27 | Cascata, métricas, Modo A/B |
| `gifi-domain-specialist` | 9 | Colunas por elo vs PRD |
| `python-developer` | 1,3–5,8,11,13,17,20,23,28–29 | Bootstrap, CLI, packages |
| `test-generator` | 30–36 | AT coverage |

---

## Code Patterns

### Pattern 1: L2Bundle loader

```python
from dataclasses import dataclass
from pathlib import Path
import json
import pandas as pd

@dataclass(frozen=True)
class L2Bundle:
    train: pd.DataFrame
    holdout: pd.DataFrame
    manifest: dict
    dataset_version: str
    schema_version: str
    source_hash: str
    paths: dict[str, Path]

def load_l2_bundle(l2_root: Path) -> L2Bundle:
    pointer = json.loads((l2_root / "current.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(pointer["manifest"]).read_text(encoding="utf-8"))
    train = pd.read_parquet(pointer["paths"]["train_features"])
    holdout = pd.read_parquet(pointer["paths"]["holdout_features"])
    return L2Bundle(
        train=train,
        holdout=holdout,
        manifest=manifest,
        dataset_version=pointer["dataset_version"],
        schema_version=pointer["schema_version"],
        source_hash=manifest["source_hash"],
        paths={k: Path(v) for k, v in pointer["paths"].items()},
    )
```

### Pattern 2: Feature matrix cleaning

```python
def build_matrix(df: pd.DataFrame, elo: str, specs: dict, *, optional_median: dict | None = None) -> tuple[pd.DataFrame, pd.Series, dict]:
  """Returns X, y, exclusions counts. Drops rows with NaN y or required features."""
  spec = specs[elo]
  y = pd.to_numeric(df[spec["target"]], errors="coerce")
  mask = y.notna()
  exclusions = {"na_target": int((~mask).sum())}
  cols = [c for c in spec["features"] if c in df.columns]
  X = df.loc[mask, cols].apply(pd.to_numeric, errors="coerce")
  req = [c for c in spec["features"] if c not in spec.get("optional_features", [])]
  bad = X[req].isna().any(axis=1)
  exclusions["na_feature"] = int(bad.sum())
  X = X[~bad]
  y = y[mask][~bad]
  return X, y, exclusions
```

### Pattern 3: Model families (sklearn Pipeline)

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor

def make_family(name: str, random_state: int) -> Pipeline:
    if name == "baseline":
        return Pipeline([("model", DummyRegressor(strategy="mean"))])
    if name == "elasticnet":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("model", ElasticNet(alpha=0.08, l1_ratio=0.5, random_state=random_state, max_iter=5000)),
        ])
    if name == "randomforest":
        return Pipeline([
            ("model", RandomForestRegressor(
                n_estimators=200, min_samples_leaf=5, random_state=random_state, n_jobs=-1
            )),
        ])
    raise ValueError(f"unknown family: {name}")
```

### Pattern 4: Cascade inference Modo A/B

```python
def infer_cascade_row(row: dict, mode: str, pipes: dict, db_proxy_factor: float = 0.985) -> dict:
    x = dict(row)
    if mode == "A" and x.get("Carga_Alcalina") is not None:
        raise ValueError("INGEST_SCENARIO_REJECT: Carga injetada em Modo A")
    extr = x.get("Extrativo_AT") if mode == "B" and x.get("Extrativo_AT") is not None else float(
        pipes["elo1"].predict([_x1(x)])[0]
    )
    x["Extrativo_AT"] = extr
    carga = x.get("Carga_Alcalina") if mode == "B" and x.get("Carga_Alcalina") is not None else float(
        pipes["elo2"].predict([_x2(x)])[0]
    )
    x["Carga_Alcalina"] = carga
    if x.get("DB_LAB") is None and x.get("DB_SGF") is not None:
        x["DB_LAB"] = db_proxy_factor * float(x["DB_SGF"])
    tsa = float(pipes["elo3"].predict([_x3(x)])[0])
    return {"Extrativo_AT": extr, "Carga_Alcalina": carga, "TSA_dia": tsa, "mode": mode}
```

### Pattern 5: Configuration (`config/simulation.yaml`)

```yaml
# Autor: Emerson Antônio | Data: 2026-07-10
repo_root: "."
l2_root: "data/l2"
models_root: "models"
logs_root: "logs/simulation"
expected_schema_version: "1.0.0"
random_state: 42
families: [baseline, elasticnet, randomforest]
holdout:
  start: "2025-05-01"
  end: "2025-10-30"
mae_limit_report: 56.0          # informativo L3; gate na Camada 4
db_proxy_factor: 0.985
io:
  read_timeout_s: 120
  lock_timeout_s: 30
  max_retries: 3
elo_specs:
  elo1:
    target: Extrativo_AT
    features: [pct_A, pct_B, pct_C, pct_D, pct_MG, pct_ABC, pct_CDMG, mix_entropy, mix_hhi, dom_A, dom_B, dom_C, dom_D, dom_MG, Idade]
  elo2:
    target: Carga_Alcalina
    features: [Extrativo_AT, TPC, DB_SGF]
  elo3:
    target: TSA_dia
    features: [pct_ABC, pct_CDMG, mix_entropy, mix_hhi, DB_LAB, Extrativo_AT, Carga_Alcalina, TPC, VMI, Volume_m3, Kappa]
    optional_features: [Casca_pct]
```

---

## Data Flow

```text
1. simulate train
   │
   ├─► load_l2_bundle(current.json)
   ├─► guard_schema + guard_holdout_eligible
   ├─► build matrices (train / holdout)
   ├─► for each elo × family: fit pipeline
   ├─► select champion per elo (min MAE holdout isolated)
   ├─► evaluate cascade Mode A on holdout → MAE_TSA_cascade
   ├─► write metrics_holdout.json + explainability.json
   └─► package → models/candidates/{run_id}/ + current_candidate.json

2. simulate infer --cenario-id X --mode A|B
   │
   ├─► load current_candidate.json
   ├─► read data/l2/scenarios/{id}/infer_features.parquet
   └─► infer_cascade per row → predictions.parquet

3. simulate evaluate [--run-id]
   │
   └─► re-score holdout com joblibs existentes (sem re-fit)
```

---

## Integration Points

| System | Type | Contract |
|--------|------|----------|
| Ingest L2 | Filesystem | `current.json`, Parquet, `batch_manifest.json` |
| Camada 4 | Filesystem | `models/candidates/{run_id}/candidate_manifest.json` |
| Camada 5 | Python import / CLI | `simulate infer` output Parquet |
| KB YAML | Read-only | `ml-tabular`, `gifi-domain`, `gifi-ingest` specs |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | ATs |
|-----------|-------|-------|-------|-----|
| Unit | metrics, guard, inference | `test_metrics`, `test_l2_guard`, `test_cascade_inference` | pytest | AT-004..008 |
| Integration | train pipeline mini L2 | `test_train_pipeline` | pytest | AT-001,003,012,015 |
| Smoke | L2 Excel real | `test_integration_l2` `@slow` | pytest | AT-001,002,014 |
| Perf | infer 500 rows | manual / `@slow` | time perf_counter | AT-011 |

**Fixture strategy:** `tests/simulation/fixtures/l2_mini/` com 20 linhas train + 5 holdout sintéticas; não depende de Excel.

---

## Error Handling

| Error / Signal | Handling | Retry? |
|----------------|----------|--------|
| `current.json` missing | Fail fast com mensagem | Não |
| `SchemaVersionError` | Bloqueia train/infer | Não |
| `holdout_eligible=false` | Bloqueia train; infer permitido com warning | Não |
| Coluna alvo ausente no L2 | Fail com lista de colunas | Não |
| `INGEST_SCENARIO_REJECT` (Modo A) | Erro inferência | Não |
| Package mid-failure | `rmtree(.staging_*)`; backup pointer intacto; log `simulate_fail` | Re-run train |
| Lock timeout | `TimeoutError` após `lock_timeout_s` | Retry manual |
| I/O transient | Retry 3× backoff em read/write Parquet e joblib | Sim |
| `TrainingDataError` (<50 rows/elo) | Abort train; sem package | Fix L2 |
| MAE_TSA > 56 | Package com `release_ok=false`; não promove pointer | CD itera features |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `GIFI_REPO_ROOT` | env | cwd | Raiz do repo |
| `l2_root` | path | `data/l2` | Entrada L2 |
| `models_root` | path | `models` | Saída candidatos |
| `expected_schema_version` | semver | `1.0.0` | Major lockstep |
| `random_state` | int | 42 | Reprodutibilidade |
| `families` | list | baseline, en, rf | Candidatos |
| `mae_limit_report` | float | 56.0 | Referência Matriz A |
| `db_proxy_factor` | float | 0.985 | Inferência cenário |
| `io.lock_timeout_s` | int | 30 | Lock `models/.train.lock` |
| `io.max_retries` | int | 3 | Retry I/O Parquet/joblib |

---

## Security Considerations

- Artefatos `models/` locais; sem secrets no manifesto
- **Joblib:** `load_pipeline()` valida `path.resolve().is_relative_to(models_root.resolve())`; rejeita symlinks fora do allowlist
- Nunca deserializar joblib de upload do usuário ou paths CLI arbitrários
- Logs sem PII; apenas `run_id`, métricas e hashes
- `chmod 750` em `models/candidates/` (opcional MVP local)

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | JSON estruturado `simulate_start` / `simulate_end` em `logs/simulation/` |
| Fields | `run_id`, `l2_dataset_version`, `l2_source_hash`, `duration_ms`, `mae_tsa_cascade`, `families_selected` |
| Metrics | `metrics_holdout.json` por candidato |

---

## Elo Feature Specs (normativo MVP)

| Elo | y | X obrigatórias | X opcionais |
|-----|---|----------------|-------------|
| 1 | `Extrativo_AT` | mix A–MG, `pct_ABC`, `pct_CDMG`, `mix_entropy`, `mix_hhi`, `dom_*`, `Idade` | — |
| 2 | `Carga_Alcalina` | `Extrativo_AT`, `TPC`, `DB_SGF` | — |
| 3 | `TSA_dia` | mix B/C, `DB_LAB`, `Extrativo_AT`, `Carga_Alcalina`, `TPC`, `VMI`, `Volume_m3`, `Kappa` | `Casca_pct` |

**Sparse targets:** linhas com `y` NaN são excluídas por elo com contagem no manifesto (`exclusions.elo{n}_na_target`).

**Elo 1b:** ausente — sem código, sem joblib.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | design-agent | Design inicial Camada 3 |
| 1.1 | 2026-07-10 | design-agent | Judge run 1: lock, matrix cleaning, rollback, joblib allowlist, I/O retry |

---

## Judge Verdict (OpenRouter — `openai/gpt-4o`, advisory)

**Run 1:** FAIL (confidence 0.85) — concorrência pointer, NaN em matrices, rollback, joblib security, I/O timeout.

**Fixes aplicados (v1.1):**

| Concern | Resposta |
|---------|----------|
| Race em `current_candidate.json` | Decision 7: `fcntl` lock + `atomic_write_json` + `.previous` backup |
| NaN / missing em features | Decision 8: `build_matrix` com exclusions + mínimo 50 linhas/elo |
| Rollback package | Decision 7: staging + rmtree; pointer intacto |
| Joblib deserialization | Decision 9: path allowlist sob `models_root` |
| I/O timeout/retry | `io.*` config + retry 3× (padrão ingest) |

> Modo **advisory**: FAIL não bloqueia `/build`. Débito Marco 2: lock distribuído multi-host.

---

## Open Questions (resolved in this design)

| # | Question | Resolution |
|---|----------|------------|
| 1 | Grain diário | Adiado — turno no Marco 1 |
| 2 | Champion strategy | Por elo, famílias heterogêneas |
| 3 | Explicabilidade | Básica L3; SHAP Camada 4 |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_SIMULATION_ENGINE.md`

**Fase Build sugerida (incremental):**

1. Bootstrap `pyproject.toml` + `config/simulation.yaml` + `SimulationSettings`
2. L2 loader + guards + testes AT-004/005
3. Features + metrics + families
4. Trainer + selector + evaluator
5. Package atômico + `simulate train`
6. Cascade infer Modo A/B + CLI infer/evaluate
7. Smoke `test_integration_l2` com `data/l2_excel_validation` ou ingest local

# DESIGN: Ingest Engine (Camada 2 GIFI)

> Arquitetura técnica para implementar I1–I5: dual-path batch/online, artefatos L2 Parquet+JSON, sinais, quarentena e remediação.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | INGEST_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (design-agent) |
| **DEFINE** | [DEFINE_INGEST_ENGINE.md](./DEFINE_INGEST_ENGINE.md) |
| **Status** | Shipped |
| **Stack** | Python 3.11+, pandas, pyarrow, pydantic v2, PyYAML, openpyxl, typer, pytest |

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGEST ENGINE (Camada 2)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─── BATCH (histórico) ───────────────────────────────────────────────┐    │
│  │ Excel/TI ──► I1 ──► I2 ──► I3 ──► I4 ──► data/l2/published/...     │    │
│  │                  │ fail │                                           │    │
│  │                  └──► I5 quarantine + remediation + logs           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─── ONLINE (cenário) ────────────────────────────────────────────────┐    │
│  │ Upload CSV/XLSX ──► I1 scenario ──► I2 light ──► infer_features    │    │
│  │                      (template_cenario_v0)     │ reject → UI reason  │    │
│  │                      SEM quarentena / remediação                     │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  KB contracts (read-only): docs/kb/gifi-ingest/specs/*.yaml                 │
│                            docs/kb/gifi-domain/specs/*.yaml                 │
│                                                                              │
│  Consumers: Camada 3 (Motor) · Camada 4 (Confiança) · Camada 5 (UI)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Package path | Purpose | Maps to |
|-----------|--------------|---------|---------|
| **Contracts** | `src/ingest/contracts/` | Carregar YAML normativo (features, sinais, warnings, template) | Pré-I1 |
| **I1 Connectors** | `src/ingest/connectors/` | Excel QM×Processo, TI stub, upload cenário | I1 |
| **I2 Validation** | `src/ingest/validation/` | Schema, unidades, mix, Modo A/B, faixas | I2 |
| **I3 Transform** | `src/ingest/transform/` | Imputação DB, mix A/B/C, turno→dia derivado, filtros | I3 |
| **I4 Publish** | `src/ingest/publish/` | Parquet, manifesto, holdout split, last-good pointer | I4 |
| **I5 Observability** | `src/ingest/observability/` | Logs JSON, sinais, quarentena, evidência remediação | I5 |
| **Batch pipeline** | `src/ingest/batch/` | Orquestração I1→I5 assíncrona | §1.1 histórico |
| **Online API** | `src/ingest/online/` | Validação síncrona cenário + `infer_features` | §1.1 online |
| **CLI** | `src/ingest/cli.py` | `ingest batch`, `ingest scenario`, `ingest reprocess` | Operação MVP |

---

## Key Decisions

### Decision 1: Layout físico L2 (`data/l2/`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE aberto #2 — paths Parquet/manifesto/quarentena não especificados.

**Choice:**

```text
data/l2/
  current.json                 # pointer: last published_ok paths + schema_version
  published/{dataset_version}/
    train_features.parquet
    holdout_features.parquet
    batch_manifest.json
  scenarios/{cenario_id}/
    infer_features.parquet
    scenario_manifest.json
  quarantine/{batch_id}/
    source_copy_or_ref.json
    violation_sample.json
    batch_manifest.json
  remediation/
    {remediation_id}.json
  triggers/
    accept_data_reject.json    # escrito pela Camada 4; lido pelo CLI reprocess
```

**Rationale:** Versionamento por `dataset_version` ISO; `current.json` implementa fallback `keep_last_published_ok` sem sobrescrever diretórios.

**Alternatives Rejected:**
1. Único diretório `data/l2/latest/` — rejeitado: perde histórico e auditoria
2. S3 desde o MVP — rejeitado: YAGNI local-first

**Consequences:**
- `data/l2/` no `.gitignore` (artefatos gerados)
- Camada 3 lê `data/l2/current.json` para resolver paths

---

### Decision 2: Grain turno no artefato publicado (sem `train_features_daily`)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE default MVP — agregação D-C em I3; Camada 3 pode precisar turno.

**Choice:** `train_features` e `holdout_features` permanecem em grain **`(data_processo, turno)`**. I3 calcula colunas derivadas diárias apenas quando necessário para regras de negócio (ex.: `TSA_dia` como meta consolidada por dia na mesma grain turno, ou coluna auxiliar `tsa_meta_dia` replicada por turno). **Não** publicar `train_features_daily` no Marco 1.

**Rationale:** Alinha `artifact-contract.yaml`, Elo 1–3 em grain turno, e `turno-dia-aggregation.md` (“treino permanece em turno”).

**Alternatives Rejected:**
1. Publicar só grain diário — rejeitado: perde resolução para Matriz A por turno
2. Dois artefatos turno+dia — rejeitado: escopo extra; adiar Marco 2

---

### Decision 3: `ACCEPT_DATA_REJECT` via trigger file + CLI

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** DEFINE aberto #3 — quem dispara reprocesso quando Camada 4 devolve lote.

**Choice:** Camada 4 escreve trigger; operador executa CLI. **Claim atômico:** `os.replace(trigger.json, triggers/processed/{id}.json)` sob lock `fcntl` (Unix) antes do reprocesso — evita double-processing.

**Rationale:** MVP sem message bus; rastreável; compatível com jobs manuais (A-004). Lock file `triggers/.lock` serializa `reprocess` (único operador CD no MVP).

**Alternatives Rejected:**
1. Polling HTTP Camada 4→Ingest — rejeitado: acoplamento prematuro
2. Reprocesso automático — rejeitado: CD deve diagnosticar antes (fluxo decisão DEFINE)
3. Banco SQLite para triggers — rejeitado: YAGNI; file+lock suficiente Marco 1

---

### Decision 4: Contratos YAML lidos de `docs/kb/` (single source of truth)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** `ContractLoader` resolve paths relativos à raiz do repo (`REPO_ROOT`). Não duplicar YAML em `src/`.

**Rationale:** Evita drift entre KB AgentSpec e código; alteração normativa = bump KB + testes.

**Consequences:** Testes usam `REPO_ROOT` fixture; deploy empacota `docs/kb/` junto.

---

### Decision 5: Pydantic para validação I2; pandas para I3/I4

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** Modelos Pydantic por grain (HistoricalRow, ScenarioRow); transformação tabular em pandas; escrita Parquet via pyarrow.

**Rationale:** Alinha AgentSpec `data-quality/schema-validation`; performance adequada para ~100k linhas.

---

### Decision 6: Online path sem FastAPI no Marco 1 ingest

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Choice:** `ScenarioValidator.validate_file(path) -> ValidationResult` como biblioteca pura. Camada 5 (FastAPI) importa este módulo. CLI `ingest scenario validate` para testes.

**Rationale:** Separação Camada 2/5; AT-017 (isolamento batch/online) — sem lock compartilhado além de filesystem read-only nos contratos.

**Alternatives Rejected:**
1. FastAPI dentro de `src/ingest/` — rejeitado: fronteira Camada 5

---

### Decision 7: Publish atômico (staging + replace) e rollback batch

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-10 |

**Context:** Judge design — risco de `current.json` corrompido ou publish parcial.

**Choice:**

1. Escrever em `published/{version}/.staging/`; validar manifesto + Parquet legíveis.
2. `os.replace(staging_dir, final_dir)` (atômico no mesmo filesystem).
3. Atualizar `current.json` via write `current.json.tmp` + `os.replace`.
4. Manter `current.json.previous` (cópia do pointer anterior) antes de cada swap bem-sucedido.
5. Em falha mid-pipeline: não tocar `current.json`; artefatos parciais ficam em `.staging/` descartável.

**Rationale:** Last-good preservado mesmo se processo morrer entre Parquet writes; rollback = restaurar `current.json.previous`.

**Consequences:**
- Novo módulo `src/ingest/publish/atomic_io.py`
- Teste AT: kill simulado após staging → `current.json` inalterado

---

## Data Flow

### Batch histórico

```text
1. CLI: ingest batch --source excels/...xlsx
2. I1: read → DataFrame + BatchIdentity(source_hash, period)
3. I2: validate rows → SignalCollector (blocking stops)
4. I3: impute DB, mix features, filter TSA<1000, derive flags
5. I4: split holdout 2025-05..2025-10; write Parquet; evaluate warning matrix
6. I5: if blocking → quarantine/; else atomic publish → update current.json
7. On exception after staging: discard `.staging/`, leave current.json untouched (rollback implicit)
8. Log ingest_end JSON stdout + optional logs/ingest/
```

### Online cenário

```text
1. UI/CLI envia arquivo + cenario_id
2. I1 scenario: parse CSV/XLSX
3. I2: template_cenario_v0 + mode A/B rules
4. Se OK: I3 light (map to feature columns) → infer_features.parquet em scenarios/{id}/
5. Se FAIL: INGEST_SCENARIO_REJECT + lista de erros legíveis (sem quarentena)
6. Log ingest_end path=scenario_online com sla_ms
```

---

## File Manifest

| # | File | Action | Purpose | Agent | Deps |
|---|------|--------|---------|-------|------|
| 1 | `pyproject.toml` | Create | Projeto Python, deps, script `ingest` | python-developer | — |
| 2 | `src/ingest/__init__.py` | Create | Package root | python-developer | — |
| 3 | `src/ingest/config.py` | Create | `IngestSettings` (paths, REPO_ROOT) | python-developer | — |
| 4 | `src/ingest/contracts/loader.py` | Create | Carrega YAML KB | gifi-ingest-engineer | 3 |
| 5 | `src/ingest/contracts/models.py` | Create | Tipos: ArtifactMeta, BatchIdentity, Signal | gifi-ingest-engineer | 4 |
| 6 | `src/ingest/observability/signals.py` | Create | Enum + SignalCollector | gifi-ingest-engineer | 4 |
| 7 | `src/ingest/observability/logging.py` | Create | JSON structured logs | gifi-ingest-engineer | 6 |
| 8 | `src/ingest/observability/quarantine.py` | Create | Isolamento lote | gifi-ingest-engineer | 6,7 |
| 9 | `src/ingest/observability/remediation.py` | Create | Evidência JSON | gifi-ingest-engineer | 4,7 |
| 10 | `src/ingest/validation/schema.py` | Create | Colunas/tipos feature-columns | gifi-ingest-engineer | 4,5 |
| 11 | `src/ingest/validation/domain_rules.py` | Create | Mix, DB range, TSA filter rules | gifi-domain-specialist | 4,10 |
| 12 | `src/ingest/validation/scenario.py` | Create | template_cenario_v0 Modo A/B | gifi-domain-specialist | 4,10 |
| 13 | `src/ingest/validation/warnings.py` | Create | warning-matrix evaluator | gifi-ingest-engineer | 4,6 |
| 14 | `src/ingest/connectors/excel_qm.py` | Create | Leitor Excel consolidado | gifi-ingest-engineer | 4,5 |
| 15 | `src/ingest/connectors/ti_stub.py` | Create | Stub TI (NotImplemented → fallback) | gifi-ingest-engineer | 14 |
| 16 | `src/ingest/connectors/scenario_upload.py` | Create | Parse upload cenário | gifi-ingest-engineer | 4 |
| 17 | `src/ingest/transform/imputation.py` | Create | DB 0.985×SGF + flags | gifi-ingest-engineer | 11 |
| 18 | `src/ingest/transform/mix_features.py` | Create | pct_ABC, entropy, HHI, dom_X | gifi-ingest-engineer | 11 |
| 19 | `src/ingest/transform/aggregation.py` | Create | Turno→dia derivado (D-C) | gifi-ingest-engineer | 17 |
| 20 | `src/ingest/transform/pipeline.py` | Create | Orquestra I3 | gifi-ingest-engineer | 17,18,19 |
| 21 | `src/ingest/publish/manifest.py` | Create | batch_manifest.json | gifi-ingest-engineer | 5,6 |
| 22 | `src/ingest/publish/atomic_io.py` | Create | staging, replace, lock, backup pointer | gifi-ingest-engineer | — |
| 23 | `src/ingest/publish/parquet_writer.py` | Create | Escrita Parquet + schema lock | gifi-ingest-engineer | 5,10 |
| 24 | `src/ingest/publish/holdout.py` | Create | Partição 2025-05..2025-10 | gifi-ingest-engineer | 13 |
| 25 | `src/ingest/publish/publisher.py` | Create | last-good, semver guard, rollback | gifi-ingest-engineer | 21,22,23,24 |
| 26 | `src/ingest/batch/pipeline.py` | Create | I1→I5 batch | gifi-ingest-engineer | 14–25,8,9 |
| 27 | `src/ingest/online/validator.py` | Create | Validação síncrona | gifi-ingest-engineer | 12,16 |
| 28 | `src/ingest/online/infer_publish.py` | Create | infer_features cenário | gifi-ingest-engineer | 20,23 |
| 29 | `src/ingest/cli.py` | Create | typer CLI | python-developer | 26,27 |
| 30 | `config/ingest.yaml` | Create | Paths default, holdout window | gifi-ingest-engineer | — |
| 31 | `tests/ingest/conftest.py` | Create | Fixtures, REPO_ROOT | test-generator | — |
| 32 | `tests/ingest/fixtures/synthetic_historical.csv` | Create | 10 linhas AT-001..004 | test-generator | — |
| 33 | `tests/ingest/fixtures/scenario_mode_a_bad.csv` | Create | AT-009 | test-generator | — |
| 34 | `tests/ingest/fixtures/scenario_mode_b_ok.csv` | Create | AT-010 | test-generator | — |
| 35 | `tests/ingest/test_validation.py` | Create | I2 unit | test-generator | 10–12 |
| 36 | `tests/ingest/test_transform.py` | Create | I3 unit TC-P01/08/A02 | test-generator | 17–19 |
| 37 | `tests/ingest/test_publish.py` | Create | I4 atomic publish, holdout, rollback | test-generator | 22,25 |
| 38 | `tests/ingest/test_batch_pipeline.py` | Create | AT-001,006,007,012 | test-generator | 26 |
| 39 | `tests/ingest/test_scenario_online.py` | Create | AT-009,010,017 | test-generator | 27,28 |
| 40 | `tests/ingest/test_integration_excel.py` | Create | Smoke Excel real (slow) | test-generator | 26 |
| 41 | `.gitignore` | Modify | `data/l2/`, `logs/ingest/` | python-developer | — |

**Total Files:** 41

**Build order (caminho crítico):** 1→4→6→10→11→14→17→18→20→21→22→23→25→26→29

---

## Agent Assignment Rationale

| Agent | Files | Why |
|-------|-------|-----|
| **gifi-ingest-engineer** | 4–9, 13–27, 29 | Dono I1–I5, sinais, publish, dual-path |
| **gifi-domain-specialist** | 11–12 | Regras Camada 1, template Modo A/B |
| **python-developer** | 1–3, 28, 40 | Bootstrap projeto, CLI, tooling |
| **test-generator** | 30–39 | AT-001..017, fixtures sintéticas |
| **data-quality-analyst** | review 10–13 | Gates qualidade (consulta) |

---

## Code Patterns

### Pattern 1: Contract loader

```python
from __future__ import annotations
from pathlib import Path
import yaml

class ContractLoader:
    def __init__(self, repo_root: Path) -> None:
        self._root = repo_root
        self._kb = repo_root / "docs" / "kb"

    def feature_columns(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "feature-columns.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def warning_matrix(self) -> dict:
        path = self._kb / "gifi-ingest" / "specs" / "warning-matrix.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def scenario_template(self) -> dict:
        path = self._kb / "gifi-domain" / "specs" / "template_cenario_v0.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))
```

### Pattern 2: Signal collector (I5)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class Severity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"

@dataclass
class IngestSignal:
    code: str
    severity: Severity
    message: str
    row_ref: str | None = None

@dataclass
class SignalCollector:
    signals: list[IngestSignal] = field(default_factory=list)

    def emit(self, code: str, severity: Severity, message: str, row_ref: str | None = None) -> None:
        self.signals.append(IngestSignal(code, severity, message, row_ref))

    @property
    def has_blocking(self) -> bool:
        return any(s.severity == Severity.BLOCKING for s in self.signals)

    def codes(self) -> list[str]:
        return [s.code for s in self.signals]
```

### Pattern 3: Atomic publish (I4)

```python
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone

def atomic_write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)  # atomic on POSIX

def publish_batch(
    out_dir: Path,
    current_pointer: Path,
    staging_artifacts: dict[str, Path],
    manifest: dict,
    signals,
) -> None:
    if signals.has_blocking:
        raise PublishBlockedError("blocking signals present")

    version = manifest["dataset_version"]
    staging = out_dir / "published" / version / ".staging"
    final = out_dir / "published" / version
    staging.mkdir(parents=True, exist_ok=True)

    for name, src in staging_artifacts.items():
        dest = staging / f"{name}.parquet"
        dest.write_bytes(src.read_bytes())

    atomic_write_json(staging / "batch_manifest.json", manifest)

    # Swap staging → final (atomic directory replace via rename parent contents)
    if final.exists():
        raise PublishConflictError(f"version already exists: {version}")
    os.replace(staging, final)

    if manifest["publish_status"] in ("published_ok", "published_with_warnings"):
        if current_pointer.exists():
            atomic_write_json(
                current_pointer.with_name("current.json.previous"),
                json.loads(current_pointer.read_text(encoding="utf-8")),
            )
        pointer = {
            "dataset_version": version,
            "schema_version": manifest["schema_version"],
            "paths": {k: str(final / f"{k}.parquet") for k in staging_artifacts},
            "manifest": str(final / "batch_manifest.json"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write_json(current_pointer, pointer)
```

### Pattern 4: Scenario online validate

```python
from __future__ import annotations
import pandas as pd
from ingest.validation.scenario import ScenarioValidator
from ingest.contracts.loader import ContractLoader

def validate_scenario_upload(path: str, repo_root) -> dict:
    loader = ContractLoader(repo_root)
    template = loader.scenario_template()
    df = pd.read_csv(path)  # ou read_excel
    validator = ScenarioValidator(template)
    errors = validator.validate_dataframe(df)
    if errors:
        return {
            "ok": False,
            "signal": "INGEST_SCENARIO_REJECT",
            "errors": errors,
        }
    return {"ok": True, "row_count": len(df)}
```

### Pattern 5: Configuration (`config/ingest.yaml`)

```yaml
# Autor: Emerson Antônio | Data: 2026-07-10
repo_root: "."  # override via GIFI_REPO_ROOT
l2_root: "data/l2"
logs_root: "logs/ingest"
schema_version: "1.0.0"
holdout:
  start: "2025-05-01"
  end: "2025-10-30"
train_cutoff: "2025-04-30"
online:
  max_rows: 500
  sla_p95_ms: 3000
db_proxy_factor: 0.985
tsa_train_min: 1000
mix_tolerance: 0.02
```

---

## Integration Points

| External System | Integration Type | Auth | Notes |
|-----------------|------------------|------|-------|
| Excel QM×Processo | File read (`excels/*.xlsx`) | Filesystem | Fonte MVP em `excels/` |
| TI interpolada | Stub → future DB/Parquet | TBD | `ti_stub.py` levanta fallback |
| Camada 3 Motor | Read Parquet via `current.json` | Local | Major schema guard no loader L3 |
| Camada 4 Confiança | Read holdout + manifest | Local | `ACCEPT_DATA_REJECT` trigger file |
| Camada 5 UI | Import `online.validator` | N/A | Sem HTTP no ingest Marco 1 |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Maps AT |
|-----------|-------|-------|-------|---------|
| Unit | I2 rules, mix, DB proxy | `test_validation.py`, `test_transform.py` | pytest | AT-002,003,004,006 |
| Unit | Warning matrix, holdout split | `test_publish.py` | pytest | AT-005,008,011,015 |
| Integration | Batch pipeline E2E | `test_batch_pipeline.py` | pytest + tmp_path | AT-001,007,012,014,016 |
| Integration | Scenario online | `test_scenario_online.py` | pytest | AT-009,010,017 |
| Smoke | Excel real 100 linhas | `test_integration_excel.py` | pytest `@pytest.mark.slow` | A-001 validation |
| Benchmark | p95 online 500 linhas | `test_scenario_online.py` | pytest-benchmark (optional) | NFR-ING-01 |

**Fixtures:** sintéticos em `tests/ingest/fixtures/` (A-005 contingency). Excel completo: `excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx` — apenas testes slow locais.

**Coverage goal:** 80% em `src/ingest/validation`, `transform`, `publish` (core path).

---

## Error Handling

| Error / Signal | Handling | Retry? |
|----------------|----------|--------|
| `INGEST_SOURCE_MISSING` | Bloqueante; log + fail fast | Sim (nova entrega TI) |
| `INGEST_SCHEMA_FAIL` | Quarentena batch | Após fix fonte |
| `INGEST_MIX_FAIL` | Bloqueante I2 | Após fix mix |
| `INGEST_UNIT_FAIL` | Quarentena + remediation | Após republicação TI |
| `INGEST_SCENARIO_REJECT` | Online: erro UI; sem quarentena | Usuário corrige upload |
| `INGEST_PROXY_DB` / sparse | Warning; warning-matrix decide | N/A |
| Publish blocked (warnings holdout) | Não atualiza `current.json` para holdout bad | CD review |
| Major schema mismatch | `SchemaVersionError` | Bump major + L4 aceite |
| I/O timeout / lock busy | Retry 3× com backoff 100–500ms | Sim |
| Publish mid-failure | Descartar `.staging/`; `current.json` intacto | Re-run batch |
| Double reprocess trigger | `fcntl` lock + move to `processed/` | Não (idempotente) |

**I/O defaults:** `read_timeout_s=120` (Excel grande), `lock_timeout_s=30` (triggers), `max_retries=3`.

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `GIFI_REPO_ROOT` | env | cwd | Raiz do repo |
| `l2_root` | path | `data/l2` | Artefatos publicados |
| `schema_version` | semver | `1.0.0` | Colunas feature |
| `holdout.start/end` | date | 2025-05..10 | Partição Matriz A |
| `online.max_rows` | int | 500 | Limite upload |
| `online.sla_p95_ms` | int | 3000 | Target NFR-ING-01 |
| `db_proxy_factor` | float | 0.985 | TC-A02 |

---

## Security Considerations

- Upload cenário: validar tamanho arquivo e `max_rows` antes de parse (DoS simples)
- Não executar macros Excel; `openpyxl` read-only
- `data/l2/quarantine/` pode conter PII operacional — **não commitar** (`.gitignore`)
- **Permissões MVP local:** criar `data/l2/` com `chmod 750`; quarantine/remediation legível só pelo usuário do pipeline (CD/TI)
- **Acesso:** sem exposição via UI; Camada 5 não lê quarantine diretamente
- **Criptografia em repouso:** fora do Marco 1 (filesystem local); documentar requisito cloud pós-MVP
- `.env` já no `.gitignore`

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | JSON lines `structured-logging.md`; `event=ingest_start\|ingest_end` |
| Signals | `SignalCollector` → manifest `warning_codes` + stdout |
| Metrics | MVP: derivar de logs (`duration_ms`, `sla_ms`); Prometheus adiar |
| Tracing | `batch_id` / `cenario_id` como correlation id |

---

## Pipeline Architecture

### DAG lógico (batch — sem Airflow Marco 1)

```text
[excel_qm] ──extract──► [raw_df] ──validate──► [clean_df]
                              │                      │
                              │                      ▼
                              │              [transform_df]
                              │                      │
                              ▼                      ▼
                        [quarantine]         [split train|holdout]
                                                      │
                                                      ▼
                                              [warning gate]
                                                      │
                                                      ▼
                                              [publish + current.json]
```

### Partition Strategy

| Artifact | Key | Granularity | Rationale |
|----------|-----|-------------|-----------|
| `train_features` | `data_processo`, `turno` | turno | Motor L3 |
| `holdout_features` | `data_processo`, `turno` | turno | Matriz A temporal |
| `infer_features` | `cenario_id`, `linha` | cenário | Modo A/B |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|----------|
| New column | major bump + L4 sign-off | Republish previous `dataset_version` from gitignored backup |
| New rule I3 only | patch `dataset_version` | Re-run batch com `source_hash` anterior |
| Type change | major bump | Restore `current.json` pointer manual |

### Data Quality Gates

| Gate | Tool | Threshold | On Failure |
|------|------|-----------|------------|
| PK not null | pandas assert | 0 nulls PK | `INGEST_SCHEMA_FAIL` |
| TSA train min | I3 filter | 0 rows < 1000 in train | AT-002 |
| Mix sum | I2 | \|sum-1\| ≤ 0.02 | `INGEST_MIX_FAIL` |
| Holdout window | I4 | 0 rows outside range | AT-005 |
| Proxy ratio holdout | warning-matrix | ≤ 20% proxy | AT-008 |
| Unknown warning | default | block | FR-ING-09 |

---

## Open Questions Resolved

| DEFINE # | Design decision |
|----------|-----------------|
| Grain diário | Turno no Parquet; sem `*_daily` Marco 1 |
| Layout físico | `data/l2/` tree acima |
| ACCEPT_DATA_REJECT | Trigger file + CLI `reprocess` |
| Amostra TI | `excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx` disponível no repo |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | design-agent | Design inicial |
| 1.1 | 2026-07-10 | design-agent | Judge run 1: Decision 7 atomic publish, trigger lock, rollback, I/O retries, security |
| 1.2 | 2026-07-10 | ship-agent | Shipped and archived |

---

## Judge Verdict (OpenRouter — `openai/gpt-4o`, advisory)

**Run 1:** FAIL — concorrência triggers, rollback batch, atomic publish, PII quarantine, I/O timeouts.  
**Run 1 fixes (v1.1):** Decision 7, Pattern 3 atômico, `atomic_io.py`, error handling expandido, security permissions.  
**Run 2 (v1.1):** FAIL residual — pede distributed lock e encryption; **aceito como débito Marco 2** (MVP local single-operator).

> Modo **advisory**: FAIL não bloqueia `/build`. Débitos documentados abaixo.

**Débito pós-MVP (não bloqueia build):**

| Item | Marco 1 | Marco 2+ |
|------|---------|----------|
| Trigger concurrency | `fcntl` + processed/ | Redis/DB lock se multi-host |
| PII quarantine | chmod 750, fora da UI | encryption at rest (cloud) |
| I/O retries | 3× backoff em atomic_io | circuit breaker / observability |

---

## Next Step

**Shipped:** `.claude/sdd/archive/INGEST_ENGINE/SHIPPED_2026-07-10.md`

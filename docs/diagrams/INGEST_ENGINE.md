# Diagramas — Ingest Engine (Camada 2)

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Feature:** INGEST_ENGINE (shipped)

---

## 1. Diagrama de classes — estrutura de dados e componentes

Modelo lógico das entidades Python, contratos KB e artefatos L2 publicados.

```mermaid
classDiagram
    direction TB

  class IngestSettings {
    +Path repo_root
    +Path l2_root
    +str schema_version
    +str holdout_start
    +str holdout_end
    +float db_proxy_factor
    +float tsa_train_min
    +float mix_tolerance
    +l2_path() Path
  }

  class ContractLoader {
    +Path _root
    +feature_columns() dict
    +warning_matrix() dict
    +artifact_contract() dict
    +scenario_template() dict
  }

  class BatchIdentity {
    +str batch_id
    +str source_path
    +str source_hash
    +str period_start
    +str period_end
    +str ingested_at
  }

  class ArtifactMeta {
    +str schema_version
    +str dataset_version
    +str source_hash
    +str publish_status
    +list warning_codes
  }

  class IngestSignal {
    +str code
    +Severity severity
    +str message
    +str row_ref
  }

  class SignalCollector {
    +list signals
    +emit(code, severity, message)
    +has_blocking bool
    +codes() list
  }

  class Severity {
    <<enumeration>>
    BLOCKING
    WARNING
    INFO
  }

  class SchemaValidator {
    +dict contract
    +normalize(df) DataFrame
    +missing_source_required(df) list
    +missing_required(df) list
  }

  class WarningMatrixEvaluator {
    +is_admitted(code, context, df) bool
    +evaluate_context(codes, context, df) tuple
  }

  class BatchManifest {
    +str schema_version
    +str dataset_version
    +str source_hash
    +str batch_id
    +dict row_counts
    +dict exclusions
    +list warning_codes
    +str publish_status
    +bool holdout_eligible
    +bool current_pointer_updated
    +str current_pointer_skip_reason
  }

  class FeatureRow {
    <<grain histórico>>
    +date data_processo
    +str turno
    +float TSA_dia
    +float DB_SGF
    +float DB_LAB
    +str db_origin
    +float pct_A..pct_MG
    +float mix_entropy
    +float Volume_m3
  }

  class TrainFeatures {
    <<Parquet>>
    +FeatureRow[] rows
    período até train_cutoff
  }

  class HoldoutFeatures {
    <<Parquet>>
    +FeatureRow[] rows
    holdout_start..holdout_end
  }

  class InferFeatures {
    <<Parquet>>
    +str cenario_id
    +int linha
    +features cenário Modo B
  }

  class CurrentPointer {
    <<JSON>>
    +str dataset_version
    +str schema_version
    +dict paths
    +str manifest
  }

  ContractLoader --> SchemaValidator : fornece feature-columns
  ContractLoader --> WarningMatrixEvaluator : fornece warning-matrix
  BatchIdentity --> BatchManifest : batch_id, source_hash
  SignalCollector --> IngestSignal : agrega
  IngestSignal --> Severity : usa
  ArtifactMeta --> BatchManifest : subset campos
  BatchManifest --> TrainFeatures : referencia
  BatchManifest --> HoldoutFeatures : referencia
  CurrentPointer --> BatchManifest : aponta manifest
  SchemaValidator --> FeatureRow : normaliza colunas
  FeatureRow <|-- TrainFeatures
  FeatureRow <|-- HoldoutFeatures
  IngestSettings --> BatchManifest : schema_version, holdout
```

### Grain e chaves

| Artefato | Chave primária | Descrição |
|----------|----------------|-----------|
| `train_features` | `data_processo` + `turno` | Treino até 2025-04-30 |
| `holdout_features` | `data_processo` + `turno` | Janela 2025-05-01 … 2025-10-30 |
| `infer_features` | `cenario_id` + `linha` | Upload cenário Modo B |
| `batch_manifest.json` | `dataset_version` | Metadados + rastreio |

### Flags de proveniência

| Coluna | Valores | Origem |
|--------|---------|--------|
| `db_origin` | `lab`, `proxy` | I3 imputation (`0,985 × DB_SGF`) |
| `publish_status` | `published_ok`, `published_with_warnings`, `quarantined` | I4 |

---

## 2. Diagrama de fluxo — pipeline batch e online

```mermaid
flowchart TB
  subgraph FONTES["Fontes de entrada"]
    EXCEL["Excel QM×Processo\n(7.573 turnos)"]
    TI["Base TI interpolada\n(stub MVP)"]
    UPLOAD["Upload cenário UI\n(CSV/XLSX)"]
  end

  subgraph I1["I1 — Connectors"]
    READ["read_qm_processo()\nnormalize + turno do horário"]
    SCN["scenario_upload"]
  end

  subgraph I2["I2 — Validation"]
    SCH["SchemaValidator\nsource / publish"]
    MIX["validate_mix / DB units"]
    WM["WarningMatrixEvaluator\ntrain | holdout | inference"]
    SCVAL["scenario Modo A/B"]
  end

  subgraph I3["I3 — Transform"]
    IMP["impute_db_lab\nproxy 0,985×SGF"]
    FEAT["derive_mix_features\nentropy, HHI, dom_X"]
    FILT["filtros TSA / mix_missing"]
  end

  subgraph I4["I4 — Publish"]
    SPLIT["split_holdout"]
    STG["staging + os.replace"]
    PQ["train_features.parquet\nholdout_features.parquet"]
    MAN["batch_manifest.json"]
    CUR["current.json\n(se holdout_eligible)"]
  end

  subgraph I5["I5 — Observability"]
    SIG["SignalCollector\nINGEST_*"]
    LOG["logs JSON estruturados"]
    QUAR["quarantine/"]
    REM["remediation-evidence"]
  end

  subgraph L2["data/l2/"]
    PUB["published/{version}/"]
    TRG["triggers/accept_data_reject.json"]
  end

  EXCEL --> READ
  TI --> READ
  READ --> SCH
  SCH --> MIX
  MIX --> IMP
  IMP --> FEAT
  FEAT --> FILT
  FILT --> SPLIT
  SPLIT --> STG
  STG --> PQ
  STG --> MAN
  MAN --> CUR
  PUB --> PQ
  PUB --> MAN

  MIX -.->|bloqueante| QUAR
  SCH -.->|bloqueante| QUAR
  SIG --> LOG
  QUAR --> REM
  TRG -->|reprocess CLI| READ

  UPLOAD --> SCN
  SCN --> SCVAL
  SCVAL -->|Modo B OK| INFER["infer_features.parquet"]
  SCVAL -.->|Modo A / inválido| REJ["INGEST_SCENARIO_REJECT"]

  WM --> MAN
  SIG --> MAN
```

### Layout L2

```text
data/l2/
├── published/{dataset_version}/
│   ├── train_features.parquet
│   ├── holdout_features.parquet
│   └── batch_manifest.json
├── current.json              ← last-good (se holdout elegível)
├── current.json.previous
├── quarantine/{batch_id}/
├── triggers/
│   ├── accept_data_reject.json
│   └── processed/
└── remediation/
```

### CLI

```bash
ingest batch <arquivo.xlsx>
ingest scenario-validate <upload.csv> --cenario-id ID
ingest scenario-publish <upload.csv> --cenario-id ID
ingest reprocess
```

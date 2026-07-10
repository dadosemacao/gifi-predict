# DEFINE: Motor de Simulação (Camada 3 GIFI)

> Cascata supervisionada Elo 1→2→3 que consome artefatos L2 (`data/l2/current.json`), treina candidatos (Baseline, ElasticNet, RandomForest), executa inferência Modo A/B e empacota métricas para o gate da Camada 4.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SIMULATION_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (define-agent) |
| **Status** | Shipped |
| **Clarity Score** | 15/15 |
| **Source** | Ingest shipped (`.claude/sdd/archive/INGEST_ENGINE/`), `docs/sketch/analytical-backbone.md`, PRD §4 |
| **Normative refs** | `docs/kb/ml-tabular/`, `docs/kb/gifi-domain/`, `docs/kb/gifi-ingest/specs/artifact-contract.yaml` |

---

## Problem Statement

A Camada 2 (Ingest Engine) já publica `train_features` e `holdout_features` versionados, mas **não existe motor** que treine a cascata Elo 1→2→3, calcule MAE por elo no holdout temporal D-A, execute inferência Modo A/B sobre `infer_features` e produza candidatos serializados para o gate A∧B∧C. Sem Camada 3, a Camada 4 não tem modelos para homologar e a Camada 5 não pode exibir curvas de TSA.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Cientista de Dados / CD Keyrus (decisor primário)** | Dono do treino e seleção de candidatos | Precisa reproduzir MAE≤56 e métricas por elo sem vazamento temporal |
| **Gate de Confiança (Camada 4)** | Consumidor de candidatos + métricas | Não pode rodar Matrizes A/B/C sem artefatos L3 empacotados |
| **Analista de planejamento (via Camada 5)** | Consome curvas TSA/Carga/Extrativos | Depende de inferência Modo A em cenários longos |
| **Ingest Engine (Camada 2)** | Produtor L2 | Exige que L3 recuse `schema_version` major divergente (contrato já definido) |

**Decisor primário em conflito:** CD Keyrus — arbitra família de modelo campeã antes de submeter à Camada 4.

**Fluxo de decisão em conflito:**

1. L3 carrega `data/l2/current.json` → valida `schema_version` e `holdout_eligible`.
2. Treina candidatos somente em `train_features`; avalia exclusivamente em `holdout_features`.
3. Se MAE holdout > 56 ou falha estrutural → candidato **não** é promovido; last champion preservado.
4. Camada 4 executa Matrizes B e C; L3 **não** declara release produtivo.

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Carregar L2 via `current.json` (`train_features`, `holdout_features`, `batch_manifest`) com guarda de `schema_version` major |
| **MUST** | Treinar cascata Elo 1 (Extrativo_AT) → Elo 2 (Carga) → Elo 3 (TSA/dia) sem Elo 1b |
| **MUST** | Comparar candidatos Baseline, ElasticNet e RandomForest por elo; reportar MAE/RMSE/WAPE |
| **MUST** | Respeitar holdout temporal D-A: treino até 2025-04-30; avaliação 2025-05-01…2025-10-30 |
| **MUST** | Implementar inferência Modo A (cascata integrada) e Modo B (injeção de Extrativo/Carga/DB_LAB) |
| **MUST** | Empacotar candidato + manifesto L3 (`model_id`, métricas, refs L2, hash) para Camada 4 |
| **SHOULD** | Inferir cenários a partir de `infer_features.parquet` publicado pelo Ingest |
| **SHOULD** | CLI `simulate train` / `simulate infer` / `simulate evaluate` |
| **COULD** | Bake-off Redes Neurais (experimento, fora do release MVP) |
| **COULD** | Agregação turno→dia pós-predição para KPIs de negócio |

---

## Success Criteria

- [ ] `simulate train` lê `data/l2/current.json` e treina 3 famílias × 3 elos sem erro quando L2 está `published_ok` ou `published_with_warnings` com `holdout_eligible=true`
- [ ] MAE holdout Elo 3 calculado na janela **2025-05-01…2025-10-30** e registrado no manifesto L3
- [ ] Relatório inclui `MAE_Extrativos`, `MAE_Carga`, `MAE_TSA` (Matriz A por elo)
- [ ] `schema_version` major ≠ esperado → erro explícito, zero linhas consumidas (NFR-ING-05 / AT-015 ingest)
- [ ] Modo A: cenário sem injeção de Carga/Extrativo → cascata completa
- [ ] Modo B: injeção de Extrativo_AT e/ou Carga respeita `template_cenario_v0` (rejeição se Modo A com campos proibidos)
- [ ] Candidato serializado em `models/candidates/{run_id}/` com manifesto JSON + joblib por elo
- [ ] Reprodutibilidade: `random_state` fixo; mesmo L2 + mesmas configs → métricas idênticas (±1e-6 float)

---

## Functional Requirements

| ID | Requirement | Component | Source |
|----|-------------|-----------|--------|
| FR-SIM-01 | Resolver paths L2 a partir de `current.json` | L3 Loader | artifact-contract, ingest shipped |
| FR-SIM-02 | Validar `schema_version` semver major antes de treinar/inferir | L3 Guard | NFR-ING-05, DEFINE ingest |
| FR-SIM-03 | Treinar Elo 1: y=`Extrativo_AT`, X=mix+Idade+sítio | Trainer E1 | cascade-regression.md |
| FR-SIM-04 | Treinar Elo 2: y=`Carga_Alcalina`, X=Extrativo_AT+TPC+DB_SGF | Trainer E2 | cascade-regression.md |
| FR-SIM-05 | Treinar Elo 3: y=`TSA_dia`, X=mix Camada B/C + qualidade + processo + Volume + Kappa | Trainer E3 | PRD §3.4–3.6 |
| FR-SIM-06 | Excluir Elo 1b (% Casca estimado); Casca só como feature Elo 3 se medida | Policy | closed-decisions D-B |
| FR-SIM-07 | Avaliar cada elo no `holdout_features` com MAE, RMSE, WAPE | Evaluator | acceptance-matrices.md |
| FR-SIM-08 | Selecionar melhor candidato por elo ou cascata conforme política CD (MAE primário) | Selector | train-select-champion.md |
| FR-SIM-09 | Inferência Modo A: predizer Extrativo→Carga→TSA em cadeia | Inference | mode-a-b-inference.md |
| FR-SIM-10 | Inferência Modo B: injetar Extrativo/Carga/DB_LAB quando presentes | Inference | mode-a-b.md |
| FR-SIM-11 | Persistir pacote candidato (joblib + manifest) referenciando `dataset_version` L2 | Packager | artifact-packaging.md |
| FR-SIM-12 | Recusar treino se `holdout_eligible=false` no manifesto L2 (Matriz A inválida) | Guard | warning-matrix, AT-008 ingest |
| FR-SIM-13 | Propagar proxy DB: usar `DB_LAB` com flag `db_origin` no feature matrix | Preprocessor | TC-A02 |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SIM-01 | Tempo treino full (7k×3 elos×3 famílias) | < 10 min em laptop CD (referência) |
| NFR-SIM-02 | Inferência cenário 500 linhas Modo A | p95 < 5s local |
| NFR-SIM-03 | Memória pico treino | < 4 GB RAM |
| NFR-SIM-04 | Rastreabilidade | Manifesto L3 referencia `source_hash` + `dataset_version` do L2 |
| NFR-SIM-05 | Determinismo | `random_state=42` default; seed configurável |

### NFR Acceptance Criteria

| NFR | Critério mensurável | Teste | Método |
|-----|---------------------|-------|--------|
| NFR-SIM-01 | Wall-clock < 600s | AT-014 | pytest benchmark opcional `@slow` |
| NFR-SIM-02 | p95 < 5000ms em 100 runs | AT-011 | script carga cenário sintético |
| NFR-SIM-04 | Campos L2 no manifesto L3 | AT-001 | assert JSON |
| NFR-SIM-05 | MAE idêntico em 2 runs | AT-015 | duplo `simulate train` |

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Carga L2 via current | `current.json` válido pós-ingest Excel | `simulate train` | Treino completa; manifesto L3 com refs L2 |
| AT-002 | Holdout temporal | L2 com 500 linhas holdout 2025-05…10 | `simulate evaluate` | Métricas só na janela D-A; zero linhas treino no holdout |
| AT-003 | MAE por elo | Candidatos treinados | evaluate | `MAE_Extrativos`, `MAE_Carga`, `MAE_TSA` presentes |
| AT-004 | Schema major mismatch | `schema_version` 2.0.0 vs motor 1.x | train | Erro `SchemaVersionError`; sem fit |
| AT-005 | Holdout inelegível | manifest L2 `holdout_eligible=false` | train | Bloqueio com mensagem; sem overwrite de candidato |
| AT-006 | Modo A integrado | `infer_features` sem Carga/Extrativo injetados | infer Modo A | Saída TSA + intermediários preditos |
| AT-007 | Modo B injeção | cenário com Extrativo e Carga fixos | infer Modo B | Elo 1/2 não sobrescrevem valores injetados |
| AT-008 | Modo A rejeita injeção | cenário Modo A com `Carga_Alcalina` preenchida | infer | Erro alinhado a `INGEST_SCENARIO_REJECT` |
| AT-009 | Proxy DB | linhas `db_origin=proxy` | train Elo 3 | Usa `DB_LAB` imputado; não falha |
| AT-010 | Elo 1b ausente | dataset sem modelo Casca | train | Nenhum artefato Elo 1b; sem erro |
| AT-011 | Performance infer | 500 linhas cenário | infer ×100 | p95 < 5s |
| AT-012 | Empacotamento | candidato com MAE holdout registrado | package | `models/candidates/{id}/manifest.json` + joblibs |
| AT-013 | TC-P01 respeitado | L2 sem TSA<1000 no train | train Elo 3 | Nenhuma linha <1000 no fit (herdado do L2) |
| AT-014 | Baseline vs EN | mesmo L2 | train | ≥2 famílias com métricas comparáveis |
| AT-015 | Determinismo | mesmo L2 e config | 2× train | MAE holdout idêntico |

**Mapeamento TC homologação (Camada 4 consome; L3 habilita):**

| TC/TM | Habilitado por L3 |
|-------|-------------------|
| TC-A01 | AT-006 (cascata integrada) |
| TC-A02 | AT-009 (proxy DB no feature matrix) |
| TC-01…08 | Features mix já no L2; L3 usa colunas Camada B/C |
| TM-01…05 | Modo B + evaluator físico (Camada 4); L3 fornece API de predição |
| TC-09/10 | Camada 4 + explicabilidade; L3 exporta contribuições básicas por feature |

---

## Out of Scope

- Implementação completa das Matrizes B e C (Camada 4 — `gifi-acceptance-engineer`)
- Release produtivo / bind na UI (Camada 5)
- Elo 1b (% Casca estimado) — NO-GO MVP (D-B)
- Retreino interativo na UI
- Redes Neurais no caminho de release (experimento opcional Marco 3+)
- Alteração de artefatos L2 ou re-ingest (escalar `gifi-ingest-engineer`)
- Caminho da Volta / feedback loop operacional

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Consumir exclusivamente L2 via `current.json` | Loader desacoplado de paths hardcoded |
| Technical | `schema_version` major lockstep com `config/simulation.yaml` | Guard obrigatório no train/infer |
| Normative | MAE≤56 é critério Camada 4; L3 reporta, não libera UI | Manifesto `release_ok=false` até gate |
| Normative | Holdout D-A fixo (decisão D-A) | Split já feito no L2; L3 não re-splita |
| Resource | MVP local single-operator | Sem cluster distribuído; joblib local |
| Timeline | Habilitar Camada 4 antes de 31/08/2026 | Marco 1 = train+evaluate+package |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `src/simulation/` | Espelha padrão `src/ingest/` |
| **Config** | `config/simulation.yaml` | schema expected, seed, model families, paths `models/` |
| **KB Domains** | `ml-tabular`, `gifi-domain`, `gifi-ingest` (read-only L2) | Patterns cascade, mode A/B, champion |
| **IaC Impact** | None (Marco 1 local) | Cloud serving = Marco 2+ |
| **Deps Python** | scikit-learn, joblib, pandas, pyarrow (já no ingest) | Adicionar ao `pyproject.toml` |

---

## Data Contract

### Source Inventory (L2 — entrada obrigatória)

| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| `train_features.parquet` | Parquet | ~7.064 turnos (ref. Excel) | `dataset_version` no manifest | Ingest I4 |
| `holdout_features.parquet` | Parquet | ~500 turnos (2025-05…10) | idem | Ingest I4 |
| `infer_features.parquet` | Parquet | ≤500 linhas/cenário | publicado online | Ingest I4 |
| `batch_manifest.json` | JSON | 1 por versão | atomically published | Ingest I4 |
| `current.json` | JSON pointer | 1 ativo | atualizado se `holdout_eligible` | Ingest I4 |

### Feature Columns (por elo — subset de `feature-columns.yaml`)

| Elo | Target (y) | Features (X) mínimas |
|-----|------------|----------------------|
| 1 | `Extrativo_AT` | `pct_A`…`pct_MG`, `pct_ABC`, `pct_CDMG`, `mix_entropy`, `mix_hhi`, `dom_*`, `Idade` |
| 2 | `Carga_Alcalina` | `Extrativo_AT`, `TPC`, `DB_SGF` |
| 3 | `TSA_dia` | Mix B/C, `DB_LAB`, `Extrativo_AT`, `Carga_Alcalina`, `TPC`, `VMI`, `Volume_m3`, `Kappa`, `Casca_pct` (se presente) |

### L3 Output Artifact (`models/candidates/{run_id}/`)

| File | Content |
|------|---------|
| `elo1.joblib`, `elo2.joblib`, `elo3.joblib` | Pipelines sklearn por elo |
| `candidate_manifest.json` | `run_id`, métricas, refs L2, família, seed, timestamps |
| `metrics_holdout.json` | MAE/RMSE/WAPE por elo |

### Freshness SLAs

| Layer | Target | Measurement |
|-------|--------|-------------|
| L2 → L3 train | Manual/CI após novo ingest | `current.json.updated_at` < train start |
| L3 candidate | Imutável após package | hash joblib no manifesto |

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | `current.json` aponta para L2 válido pós-ingest Excel | Treino falha até novo ingest | [x] Excel 2026-07-10 |
| A-002 | `Extrativo_AT` presente/sparsity aceitável no holdout | MAE Elo 1 instável; alerta Camada 4 | [ ] |
| A-003 | Grain turno é suficiente para MVP (sem agregação diária no motor) | UI pode precisar agregação Camada 5 | [x] DEFINE ingest |
| A-004 | sklearn ElasticNet/RF atendem MAE≤56 com features L2 | NN bake-off Marco 3 | [ ] |
| A-005 | `holdout_eligible=true` no L2 de produção | Bloquear train até CD reprocessar L2 | [x] manifesto Excel |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Lacuna pós-L2 clara; bloqueio Camada 4/5 |
| Users | 3 | CD decisor + consumidores L4/L5 |
| Goals | 3 | MUST/SHOULD/COULD priorizados |
| Success | 3 | Métricas numéricas, holdout, MAE por elo |
| Scope | 3 | Fronteira L3 vs L4/L5 e Elo 1b explícita |
| **Total** | **15/15** | |

---

## Open Questions

Nenhuma bloqueante para Design — defaults MVP:

1. **Grain diário pós-predição:** adiado (COULD); treino/inferência em turno.
2. **Champion único vs por elo:** DESIGN deve fixar; default = melhor família **por elo** (3 joblibs heterogêneos permitidos).
3. **Explicabilidade básica em L3:** exportar `feature_importances_` / coeficientes EN; SHAP completo fica Camada 4.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | define-agent | Versão inicial pós-ship INGEST_ENGINE |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_SIMULATION_ENGINE.md`

**Agentes sugeridos:** `gifi-simulation-engineer`, `gifi-domain-specialist`, `python-developer`, `test-generator`

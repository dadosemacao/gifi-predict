# DEFINE: Ingest Engine (Camada 2 GIFI)

> Sistema que transforma fontes brutas (Excel QM×Processo, TI, upload de cenário) em artefatos L2 versionados, auditáveis e consumíveis pela cascata e pelo gate de confiança.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | INGEST_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (define-agent) |
| **Status** | Shipped |
| **Clarity Score** | 15/15 |
| **Source** | `.claude/sdd/features/BRAINSTORM_INGEST_ENGINE.md` |
| **Normative refs** | `docs/sketch/ingest-engine.md` v1.2, `docs/PRD_GIFI_v1.1.md`, `docs/kb/gifi-ingest/`, `docs/kb/gifi-domain/specs/template_cenario_v0.yaml` |

---

## Problem Statement

A plataforma determinística GIFI (Camadas 3–5) não pode treinar, validar nem inferir sem uma representação de dados estável, versionada e auditável. Hoje não existe implementação do Ingest Engine — apenas contratos documentais — e divergências anteriores (template na UI, agregação aberta, Elo 1b) geraram risco de build incorreto. O problema é garantir que **toda entrada** (histórico batch ou cenário online) passe por validação normativa Camada 1 e produza artefatos L2 com sinais explícitos, sem sobrescrever a última versão boa em falha.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Cientista de Dados / CD Keyrus (decisor primário)** | Dono do pipeline analítico e gate de mudanças L2 | Não consegue iniciar Camada 3 sem `train_features` / `holdout_features` confiáveis; arbitra conflitos TI vs regras Camada 1 |
| TI Veracel | Fornece base QM×Processo / interpolada | Entregas com unidade errada ou atraso quebram treino sem rastreio claro |
| Analista de planejamento | Upload de cenários na UI (Camada 5) | Rejeição opaca ou lenta no upload Modo A/B |
| Motor de Simulação (Camada 3) | Consumidor de features | Join silencioso incorreto se `schema_version` divergir |
| Gate de Confiança (Camada 4) | Aceite Matriz A | Holdout temporal e warnings precisam ser objetivos, não ad hoc |

**Decisor primário em conflito:** CD Keyrus — valida exceções normativas antes de aceite Camada 4.

**Fluxo de decisão em conflito:**

1. TI entrega fonte → I2 emite sinal bloqueante → quarentena automática (sem override na UI).
2. CD diagnostica via manifesto + amostra de violação.
3. Se regra Camada 1 vs realidade operacional divergir → CD abre change request em `DECISOES_GIFI.md` (não aceite ad hoc).
4. Camada 4 só homologa após artefato `published_ok` ou `published_with_warnings` admitido na warning matrix.

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Publicar artefatos L2 (`train_features`, `holdout_features`, `infer_features`, `batch_manifest`) em Parquet+JSON com `schema_version` semver e lista fixa de colunas (`feature-columns.yaml`) |
| **MUST** | Implementar dual-path: batch histórico (quarentena + remediação) e validação online síncrona de cenário (sem quarentena) |
| **MUST** | Aplicar regras do brief: filtro TSA < 1.000, mix ±0,02, DB [350,650] kg/m³, proxy DB 0,985×SGF, features Mix A/B/C |
| **MUST** | Emitir catálogo de sinais §4.3 e matriz de warnings §3.1; warning desconhecido = bloqueante |
| **MUST** | Preservar `last_published_ok` quando lote novo falha ou entra em quarentena |
| **SHOULD** | Validar upload contra `template_cenario_v0` com p95 < 3s até 500 linhas |
| **SHOULD** | Registrar evidência de remediação (`remediation-evidence.yaml`) e logs estruturados I5 |
| **COULD** | Conector TI interpolado (fallback Excel já cobre MVP) |
| **COULD** | Orquestração Airflow após I4 estável |

---

## Success Criteria

- [ ] `train_features` e `holdout_features` publicados com `publish_status ∈ {published_ok, published_with_warnings}` e `schema_version` documentado no manifesto
- [ ] Holdout: `min(data_processo) ≥ 2025-05-01` AND `max(data_processo) ≤ 2025-10-30` AND `count(*) WHERE data_processo NOT BETWEEN ... = 0` (AT-005)
- [ ] Zero linhas com `TSA_dia < 1000` no dataset de treino publicado (TC-P01)
- [ ] Features Camada C (`mix_entropy`, `mix_hhi`, `dom_X`) calculadas e verificáveis (TC-08)
- [ ] `DB_LAB` imputado com fator 0,985 documentado via `db_origin=proxy` quando Lab ausente (TC-A02)
- [ ] Upload Modo A com `Carga_Alcalina` preenchida → `INGEST_SCENARIO_REJECT` em < 3s p95 (≤ 500 linhas)
- [ ] Lote com `INGEST_UNIT_FAIL` não substitui artefato `published_ok` anterior
- [ ] 100% dos eventos `ingest_end` batch emitem log JSON com `batch_id`, `source_hash`, `duration_ms`, `publish_status`, `signals[]`

---

## Functional Requirements

| ID | Requirement | Component | Source |
|----|-------------|-----------|--------|
| FR-ING-01 | Publicar `train_features`, `holdout_features`, `batch_manifest` em Parquet+JSON com semver | I4 | ingest-engine §4.2, artifact-contract.yaml |
| FR-ING-02 | Publicar `infer_features` a partir de upload válido Modo A/B | I4 | ingest-engine §7 |
| FR-ING-03 | Ler fontes históricas (Excel QM×Processo; TI quando disponível) com `source_hash` e metadados de lote | I1 | ingest-engine §2 I1 |
| FR-ING-04 | Validar schema, tipos, unidades e regras Camada 1 antes de transformar | I2 | PRD §3, operational-ranges |
| FR-ING-05 | Imputar `DB_LAB = 0.985 × DB_SGF` quando ausente; flag `db_origin` | I3 | DECISOES, TC-A02 |
| FR-ING-06 | Derivar `pct_AB`, `pct_DMG`, `pct_ABC`, `pct_CDMG`, entropy, HHI, `dom_X` | I3 | PRD §3.3–3.4, feature-columns.yaml |
| FR-ING-07 | Agregar turno→dia: qualidade ponderada por volume; volume soma; TSA meta diária | I3 | DECISOES D-C |
| FR-ING-08 | Validar upload online contra `template_cenario_v0.yaml` sem quarentena | I1+I2 | template_cenario_v0, §1.1 |
| FR-ING-09 | Aplicar matriz de warnings admissíveis por contexto (train/holdout/inference) | I5 | warning-matrix.yaml |
| FR-ING-10 | Isolar lote falho em quarentena; manter última versão boa | I5 | §3, artifact-contract fallback |
| FR-ING-11 | Registrar evidência de remediação (antes/depois, motivo, responsável) | I5 | remediation-evidence.yaml |
| FR-ING-12 | Emitir logs estruturados JSON por marco de ingestão | I5 | structured-logging.md |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-ING-01 | Latência validação cenário online | p95 < 3s até 500 linhas |
| NFR-ING-02 | Latência ingest histórico | Assíncrono; minutos–horas aceitável |
| NFR-ING-03 | Rastreabilidade | Todo artefato rastreável a `source_hash` + `dataset_version` |
| NFR-ING-04 | Determinismo | Mesma fonte + mesmas regras → mesmo artefato (hash reprodutível) |
| NFR-ING-05 | Compatibilidade schema | Camada 3 recusa major `schema_version` diferente do esperado |

### NFR Acceptance Criteria

| NFR | Critério mensurável | Teste | Método de validação |
|-----|---------------------|-------|---------------------|
| NFR-ING-01 | p95 `sla_ms` < 3000 em 100 uploads de 500 linhas | AT-010 + benchmark | Script de carga; percentil 95 nos logs `ingest_end` |
| NFR-ING-02 | Batch não bloqueia UI | AT-017 | Upload online completa com batch em execução paralela; p95 online ainda < 3s |
| NFR-ING-03 | 100% artefatos com `source_hash` + `dataset_version` no manifesto | AT-001, AT-012 | Assert JSON manifesto obrigatório |
| NFR-ING-04 | Hash Parquet idêntico em 2 runs com mesma fonte/regras | AT-014 | `sha256` do arquivo Parquet (excl. `dataset_version` metadata) |
| NFR-ING-05 | Major mismatch → recusa explícita | AT-011, AT-015 | Camada 3/I4 retorna erro sem join silencioso |

### Schema Version Compatibility Policy

| Mudança | Bump | Quem aprova | Comportamento |
|---------|------|-------------|---------------|
| Coluna nova | **major** obrigatório | Camada 4 (Confiança) antes de L3 consumir | I4 recusa publicação sem major; L3 recusa leitura se major ≠ esperado |
| Coluna removida / tipo alterado | **major** | Camada 4 | Idem |
| Coluna opcional preenchida (backward-compatible) | **minor** | CD registra no manifesto | L3 aceita se major igual |
| Correção de regra I3 sem mudança de coluna | **patch** `dataset_version` | CD | Mesmo `schema_version`; novo `source_hash` |

**Fronteira:** `schema_version` governa **colunas de feature** (lista em `feature-columns.yaml`). PK (`data_processo`+`turno` vs `cenario_id`+`linha`) não altera major.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Publicação treino OK | Excel histórico válido kg/m³, mix soma 1,0 | Ingest batch completa I1→I4 | `train_features` Parquet com `published_ok`; manifesto com contagens |
| AT-002 | Filtro TC-P01 | Fonte com linhas `TSA_dia < 1000` | I3 transforma e I4 publica | Zero linhas < 1000 no treino; `INGEST_FILTER_INFO` no manifesto |
| AT-003 | Proxy DB TC-A02 | Linhas sem `DB_LAB`, com `DB_SGF` | I3 imputa | `DB_LAB ≈ 0.985 × DB_SGF`; `db_origin=proxy` |
| AT-004 | Features TC-08 | Mix concentrado vs equilibrado | I3 deriva Camada C | `dom_A=1` no concentrado; `mix_hhi` maior no concentrado; `mix_entropy` maior no equilibrado |
| AT-005 | Holdout temporal | Dados 2024–2025 | I4 particiona | `holdout_features` só com `data_processo` em 2025-05..2025-10 |
| AT-006 | Mix inválido | `pct_*` soma 0,95 | I2 valida | `INGEST_MIX_FAIL`; sem publicação; last-good preservado |
| AT-007 | Unidade inválida | DB em g/cm³ | I2 valida | `INGEST_UNIT_FAIL`; quarentena; remediação registrável |
| AT-008 | Warning holdout proxy | > 20% linhas `db_origin=proxy` no holdout | I4 avalia warning matrix | Bloqueia holdout para Matriz A |
| AT-009 | Cenário Modo A rejeitado | Upload com `Carga_Alcalina` preenchida, `modo=A` | Validação online | `INGEST_SCENARIO_REJECT`; motivo legível; sem `infer_features` |
| AT-010 | Cenário Modo B aceito | Upload válido `template_cenario_v0`, `modo=B` | Validação online < 3s | `INGEST_SCENARIO_REJECT` ausente; `infer_features` Parquet publicado com mesmo `schema_version` das colunas de feature |
| AT-011 | Schema breaking | Nova coluna sem major bump | I4 tenta publicar | Publicação recusada; major bump obrigatório |
| AT-012 | Remediação | Lote bloqueante + correção TI | Reprocesso com novo hash | `remediation-evidence` com `source_hash_before/after`; `published_ok` após fix |
| AT-013 | Sparse Lab holdout | Holdout com alvo/feature crítica ausente na janela | I4 avalia `INGEST_SPARSE_LAB` | Holdout inelegível à Matriz A (`warning-matrix.yaml`); treino pode publicar com flag |
| AT-014 | Determinismo | Mesmo Excel + mesmas regras | Dois runs batch | `source_hash` e conteúdo Parquet idênticos (exclui `dataset_version` timestamp) |
| AT-015 | Major mismatch | `train_features` major 2.x; Motor espera 1.x | Camada 3 carrega | Erro explícito; nenhuma linha consumida; last-good intacto |
| AT-016 | Rastreabilidade NFR | Lote publicado | Inspecionar manifesto | `source_hash` e `dataset_version` presentes e não vazios |
| AT-017 | Isolamento batch/online | Batch longo em execução | Upload cenário 500 linhas | Validação online termina < 3s; sem lock no path online |

---

## Out of Scope

- Treino de modelos, cálculo de TSA, seleção de campeão (Camadas 3–4)
- Elo 1b (% Casca como elo separado) — NO-GO MVP (D-B)
- Quarentena ou ciclo de remediação no path online de cenário
- Airflow / DAG de orquestração no Marco 1
- Caminho da Volta, cloud em tempo real, retreino na UI, NN
- Novos agentes ou KBs de domínio ingest (cobertura existente suficiente)
- SLA formal de reprocesso quando TI republicar base (pendência §9.2)

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Normativo | Regras Camada 1 são fonte da verdade | I2/I3 não reinventam regras do PRD |
| Arquitetural | Ingest não treina nem infere TSA | Escopo estrito I1–I5 |
| Contrato | Colunas fixas em `feature-columns.yaml` | Breaking = major semver + aceite L4 |
| Dual-path | Online ≠ batch SLA | Validação leve só no upload; remediação só batch |
| Dados | Excel consolidado é fallback se TI atrasar | I1 deve suportar ambos os conectores |
| Timeline | Marco 1 backbone depende de L2 estável | Caminho crítico: contratos → I2 → I1 → I3 → I4 |
| Homologação | UI mínima até 31/08/2026 | Conector cenário (passo 7) pode ser paralelo tardio à UI |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `src/ingest/` (proposto) | Submódulos: `connectors/`, `validation/`, `transform/`, `publish/`, `observability/`; separar `batch/` e `online/` |
| **KB Domains** | `gifi-domain`, `gifi-ingest`, `spreadsheet-connectors` | Normativo local |
| **AgentSpec reuse** | `data-contracts-engineer`, `data-quality-analyst`, `python-developer`, `test-generator` | Sem agentes novos |
| **Cursor agents** | `gifi-ingest-engineer`, `gifi-domain-specialist` | Roteamento `.cursor/rules/gifi-agents.mdc` |
| **IaC Impact** | None no MVP local | Cloud/Airflow pós-Marco 1 |
| **Output formats** | Parquet (datasets), JSON (manifesto, logs, remediação) | DECISOES D-D |

**Component map (I1–I5):**

```
I1 connectors → I2 validation → I3 transform → I4 publish → Backbone L3/L4/L5
                     ↓ fail batch          ↑
                  I5 signals/logs/quarantine/remediation
I1 scenario → I2 online → infer_features (sem quarentena)
```

---

## Data Contract

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| Excel QM×Processo consolidado | XLSX/CSV | ~100k+ linhas turno | Entrega batch TI/CD | TI Veracel / CD |
| Tabelas TI interpoladas | DB/Parquet (futuro) | TBD | Quando disponível | TI |
| Upload cenário Modo A/B | CSV/XLSX | ≤ 500 linhas/upload | Online síncrono | Analista via UI |
| Contrato template | YAML `template_cenario_v0` | 1 spec versionada | Estático Camada 1 | gifi-domain |

### Published Artifacts

| Artifact | Format | Primary Key | Consumer |
|----------|--------|-------------|----------|
| `train_features` | Parquet | `data_processo`, `turno` | Camada 3 |
| `holdout_features` | Parquet | `data_processo`, `turno` | Camada 4 |
| `infer_features` | Parquet | `cenario_id`, `linha` | Camada 3, 5 |
| `batch_manifest` | JSON | `dataset_version` | Todas |

**Nota grain:** `train_features` / `holdout_features` permanecem em grain turno (`data_processo`, `turno`). A agregação turno→dia (FR-ING-07) aplica-se a métricas derivadas (ex.: TSA meta diária, qualidade ponderada); decisão sobre artefato `*_daily` separado fica no DESIGN (ver Open Questions).

Column contract: `docs/kb/gifi-ingest/specs/feature-columns.yaml` (lista fixa; proibido coluna nova sem major bump).

Provenance flags: `db_origin ∈ {lab, proxy}`; `extr_origin ∈ {medido, estimado}`.

**Compatibilidade `schema_version`:** refere-se ao conjunto de colunas de feature (tipos/unidades), não à PK. `train_features` e `infer_features` compartilham `schema_version` de colunas; PKs diferem por grain.

### Freshness SLAs

| Path | Target | Measurement |
|------|--------|-------------|
| Validação cenário online | p95 < 3s | `sla_ms` no log `ingest_end` |
| Ingest histórico batch | Assíncrono | `duration_ms` no log; sem SLA hard no MVP |
| Republicação TI | TBD (§9.2) | Fora do escopo MVP |

### Completeness Metrics

- 100% das colunas obrigatórias de treino presentes ou imputadas com flag (`db_origin`)
- Manifesto reporta `rows_excluded` para TSA < 1000
- Holdout: 0 linhas fora da janela 2025-05..2025-10

### Lineage Requirements

- `source_hash` em todo artefato e manifesto
- `remediation-evidence` liga `source_hash_before` → `source_hash_after`
- `schema_version` idêntico entre `train_features` e `infer_features` para join seguro

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Excel consolidado reflete schema QM×Processo acordado | Mapeamento I1 incorreto; retrabalho conector | [ ] |
| A-002 | Perfil de sítio via `pct_A..MG` é suficiente para Elo 1 (sem coluna `Sitio`) | Exigir coluna categórica; mudança template | [x] documentado em template_cenario_v0 |
| A-003 | Grain turno é PK canônica; agregação diária é derivada em I3 | Pode exigir artefato `*_daily` separado no DESIGN | [ ] |
| A-004 | MVP roda local sem Airflow | Jobs manuais/CLI para batch | [x] YAGNI |
| A-005 | Amostra Excel TI disponível antes do build I1 histórico | Testes de integração adiados | [ ] |

### Assumption Contingencies

| ID | Se inválida antes do build | Plano B |
|----|---------------------------|---------|
| A-001 | Schema real ≠ mapeamento documentado | CD + TI produzem `column_mapping_v0.yaml` em 1 sprint; I1 só após validação em amostra de 100 linhas |
| A-005 | Excel não disponível no repo | Testes I1 com fixture sintético mínimo (10 linhas) + integração real adiada ao Marco 1b |

---

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | L2 bloqueia L3; risco de divergência documental resolvido no sprint P0 |
| Users | 3 | CD, TI, analista, consumidores L3/L4 identificados |
| Goals | 3 | MUST/SHOULD/COULD priorizados com FR/NFR numerados |
| Success | 3 | Métricas numéricas (3s, 500 linhas, janela holdout, TCs) |
| Scope | 3 | Grain/schema_version clarificados; AT-013/014 adicionados pós-judge advisory |
| **Total** | **15/15** | ≥ 12 — pronto para Design |

---

## Open Questions

Questões para resolver na fase **Design** (não bloqueiam Define):

1. **Grain diário (default MVP):** agregação turno→dia permanece **dentro de I3**; **não** publicar `train_features_daily` no Marco 1. Reavaliar no Design se Camada 3 exigir grain diário explícito.
2. **Layout físico:** padrão de diretórios para Parquet/manifesto/quarentena (ex.: `data/l2/{dataset_version}/`).
3. **`ACCEPT_DATA_REJECT`:** evento disparado por Camada 4 — job manual, CLI ou hook assíncrono para reprocesso I1?
4. **Amostra TI:** quando o Excel real estará no repo ou ambiente de teste para fixtures I1?

---

## Traceability

| Brainstorm / Plano | DEFINE coverage |
|--------------------|-----------------|
| FR-ING-01..07 (draft) | FR-ING-01..12, NFR-ING-01..05 |
| P0 divergências D-ING-01..06 | Resolvidas em docs v1.2 / KB 0.2.4 (pré-requisito atendido) |
| P1 KB remediation + logging | FR-ING-11, FR-ING-12 |
| TC-P01, TC-08, TC-A02 | AT-002, AT-004, AT-003 |
| YAGNI | Out of Scope |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | define-agent | Versão inicial a partir de BRAINSTORM_INGEST_ENGINE.md |
| 1.1 | 2026-07-10 | define-agent | Revisão advisory pós-`--judge`: AT-013/014, grain/schema_version |
| 1.2 | 2026-07-10 | define-agent | Correções judge OpenRouter: NFR acceptance, schema policy, contingências, decisor primário |
| 1.3 | 2026-07-10 | define-agent | AT-017, fluxo decisão, default grain MVP, judge run 2 feedback |
| 1.4 | 2026-07-10 | ship-agent | Shipped and archived |

---

## Judge Verdict (OpenRouter — `openai/gpt-4o`, advisory)

**Run 1 (2026-07-10):** FAIL — NFR acceptance, schema policy, assumptions, holdout metrics, decisor primário.  
**Run 2 (v1.2):** FAIL — NFR-ING-02, assumptions A-001/A-005, grain diário, fluxo decisão.  
**Run 3 (v1.3):** contingências + AT-017 + default grain MVP + fluxo decisão 4 passos.

> Modo **advisory**: FAIL não bloqueia `/design`. API key OK; falha inicial foi **SSL** (resolvido com `SSL_CERT_FILE=$(python3 -m certifi)`).

---

## Next Step

**Shipped:** `.claude/sdd/archive/INGEST_ENGINE/SHIPPED_2026-07-10.md`

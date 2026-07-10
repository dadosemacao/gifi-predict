# DEFINE: Gate de Confiança e Aceite (Camada 4 GIFI)

> Motor de aceite que consome candidatos L3 (`models/candidates/`), executa Matrizes A∧B∧C (estatística, física, explicabilidade), aplica política de campeão e autoriza — ou bloqueia — o bind produtivo para a Camada 5.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | ACCEPTANCE_GATE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (define-agent) |
| **Status** | Design Complete |
| **Clarity Score** | 15/15 |
| **Source** | Simulation shipped (`.claude/sdd/archive/SIMULATION_ENGINE/`), `docs/sketch/analytical-backbone.md` §Camada 4, PRD §4.3 |
| **Normative refs** | `docs/kb/gifi-domain/concepts/acceptance-matrices.md`, `patterns/champion-policy.md`, `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` |

---

## Problem Statement

A Camada 3 produz candidatos com métricas de holdout (`metrics_holdout.json`) e flag informativa `release_ok`, mas **não existe gate normativo** que execute Matriz B (monotonicidade física TC/TM), Matriz C (top-3 detratores ΔTSA) nem consolide **A ∧ B ∧ C** antes de liberar a UI produtiva. Sem Camada 4, a Camada 5 não pode distinguir modo demonstração de release homologável, e o stakeholder não tem evidência auditável de conformidade com o PRD.

**Estado atual:** MAE_TSA_cascade ~94.79 no Excel real (gate A falha). A Camada 4 deve reportar o gap com evidência estruturada, não bloquear o desenvolvimento da UI em modo demo.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Cientista de Dados / CD Keyrus (decisor primário)** | Submete candidatos ao gate | Precisa de relatório A/B/C reproduzível para iterar modelo |
| **Stakeholder Veracel (Thiago)** | Homologação assistida até 31/08/2026 | Exige evidência formal antes de uso operacional |
| **Camada 5 (UI)** | Consumidor de release | Não pode bind produtivo sem `acceptance_report` verde |
| **Camada 3 (Simulation)** | Produtor de candidatos | Escalado quando falha é de modelagem, não de protocolo |

**Decisor primário em conflito:** CD Keyrus — interpreta gap de MAE e prioriza iterações; stakeholder arbitra exceções (change request).

**Fluxo de decisão:**

1. Camada 4 carrega candidato L3 (`run_id` ou último empacotado).
2. Executa Matriz A (revalida MAE holdout ≤ 56 + métricas por elo).
3. Executa Matriz B (TC-01…08 + TM-01…05 via inferência Modo A/B).
4. Executa Matriz C (TC-09/10 + top-3 detratores SHAP/coef por cenário).
5. Se **A ∧ B ∧ C** → promove para `models/champion/` + `current_champion.json`.
6. Se falha parcial → `acceptance_report.json` com flags; UI permanece em modo demo.

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Executar Matriz A: validar `MAE_TSA_cascade ≤ 56` na janela holdout D-A (2025-05…2025-10) |
| **MUST** | Executar Matriz B: TC-01…08 + TM-01…05 com direção física documentada |
| **MUST** | Executar Matriz C: top-3 detratores ΔTSA (TC-09, TC-10) com método auditável |
| **MUST** | Gate `release_ok = A ∧ B ∧ C`; nunca liberar produção com parcial |
| **MUST** | Gerar `acceptance_report.json` imutável por `run_id` + hash do candidato L3 |
| **MUST** | Promover campeão produtivo somente se gate completo (`models/champion/`) |
| **SHOULD** | CLI `accept run --run-id` / `accept report` |
| **SHOULD** | Reutilizar inferência L3 (`simulate infer`) sem duplicar cascata |
| **SHOULD** | Relatório de aderência consolidado para homologação (PDF/JSON export) |
| **COULD** | Integração futura MLflow Tracking (Marco 2 — ver ADR-003) |
| **COULD** | Bake-off NN como candidato extra (só campeão se passar A∧B∧C) |

---

## Success Criteria

- [ ] `accept run --run-id <id>` produz `acceptance_report.json` com flags `matriz_a`, `matriz_b`, `matriz_c`, `release_ok`
- [ ] Matriz A falha explicitamente quando MAE > 56 (cenário atual Excel ~94.79)
- [ ] Matriz B executa TM-01…05 e registra pass/fail por estímulo
- [ ] Matriz C retorna top-3 detratores para cenários TC-09 e TC-10
- [ ] `release_ok=true` só quando A∧B∧C; atualiza `models/current_champion.json`
- [ ] `release_ok=false` preserva last-good champion (se existir)
- [ ] Relatório referencia `l2.dataset_version`, `l3.run_id`, hashes de joblibs
- [ ] Suite pytest cobre happy path sintético + falha MAE + falha física simulada

---

## Functional Requirements

| ID | Requirement | Component | Source |
|----|-------------|-----------|--------|
| FR-ACC-01 | Carregar candidato L3 por `run_id` ou diretório `models/candidates/{id}/` | Loader | artifact-packaging.md |
| FR-ACC-02 | Validar integridade: hashes manifesto L3 vs arquivos joblib | Guard | DESIGN simulation D9 |
| FR-ACC-03 | Matriz A: revalidar `mae_tsa_cascade`, `mae_extrativos`, `mae_carga` no holdout L2 | MatrizA | acceptance-matrices.md |
| FR-ACC-04 | Matriz A: limiar rígido MAE ≤ 56 (sem "próximo a") | MatrizA | PRD §4.3, D-15 |
| FR-ACC-05 | Matriz B: executar vetores TC-01…08 (cenários por sítio/mix) | MatrizB | CASOS_TESTE §2 |
| FR-ACC-06 | Matriz B: executar monotonicidades TM-01…05 (estresse ceteris paribus) | MatrizB | physics-constraints.md |
| FR-ACC-07 | Matriz B: inferência Modo A para estresse; Modo B quando injeção exigida | Runner | mode-a-b-inference.md |
| FR-ACC-08 | Matriz C: top-3 detratores ΔTSA por cenário (SHAP RF / coef EN) | MatrizC | matriz-c-detractors.md |
| FR-ACC-09 | Matriz C: cobrir mínimos TPC, Extrativo_AT, Carga; Casca se feature ativa | MatrizC | PRD §4.3 |
| FR-ACC-10 | Política campeão: melhor MAE entre elegíveis; empate → interpretabilidade | Selector | champion-policy.md |
| FR-ACC-11 | Promover para `models/champion/{run_id}/` apenas se A∧B∧C | Publisher | champion-policy.md |
| FR-ACC-12 | Gerar `acceptance_report.json` + `acceptance_summary.md` | Reporter | adherence-report.md |
| FR-ACC-13 | Bloquear aceite se L2 `holdout_eligible=false` | Guard | ingest warning-matrix |
| FR-ACC-14 | Distinguir `demo_mode` (UI) vs `production_bind` (gate) no relatório | Policy | analytical-backbone §4 |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-ACC-01 | Tempo gate completo (1 candidato, Excel L2) | < 15 min local |
| NFR-ACC-02 | Determinismo Matriz B/C | Mesmo candidato + cenários → mesmo relatório |
| NFR-ACC-03 | Rastreabilidade | Report liga L2 + L3 + versão KB TC/TM |
| NFR-ACC-04 | Segurança | Joblib load só via paths allowlist L3 (reutilizar guard) |

### NFR Acceptance Criteria

| NFR | Critério | Teste |
|-----|----------|-------|
| NFR-ACC-01 | Wall-clock < 900s | AT-ACC-014 `@slow` |
| NFR-ACC-03 | Campos L2/L3 no report | AT-ACC-001 |
| NFR-ACC-02 | 2× `accept run` → JSON idêntico | AT-ACC-015 |

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-ACC-001 | Relatório completo | Candidato L3 válido + L2 holdout | `accept run` | `acceptance_report.json` com A/B/C flags |
| AT-ACC-002 | Matriz A pass | MAE ≤ 56 (fixture sintética) | `accept run` | `matriz_a=true` |
| AT-ACC-003 | Matriz A fail | MAE ~95 (Excel real) | `accept run` | `matriz_a=false`; `release_ok=false` |
| AT-ACC-004 | Matriz B monotonicidade | TM-01 DB↓ | stress runner | TSA não sobe |
| AT-ACC-005 | Matriz B TC-05 | TPC=30 cenário | TC runner | TSA penalizado vs baseline |
| AT-ACC-006 | Matriz C TC-09 | Cenário TPC verde | detractor engine | TPC no top-3 |
| AT-ACC-007 | Matriz C TC-10 | Cenário TC-03 stress | detractor engine | Extrativo/Carga no top-3 |
| AT-ACC-008 | Gate parcial | A=true, B=false | `accept run` | `release_ok=false`; sem champion |
| AT-ACC-009 | Promoção campeão | A∧B∧C true (fixture) | `accept run` | `models/champion/` + pointer |
| AT-ACC-010 | Last-good preservado | Gate fail com champion anterior | `accept run` | `current_champion.json` intacto |
| AT-ACC-011 | Holdout inelegível L2 | `holdout_eligible=false` | `accept run` | Erro; sem relatório final |
| AT-ACC-012 | Hash mismatch joblib | arquivo corrompido | `accept run` | Erro integridade |
| AT-ACC-013 | Demo vs prod flag | gate fail | report | `production_bind=false`, `demo_mode=true` |
| AT-ACC-014 | Performance gate | candidato Excel | `accept run` | < 15 min |
| AT-ACC-015 | Determinismo | mesmo run_id 2× | `accept run` | relatório idêntico |

**Mapeamento homologação oficial:**

| TC/TM | Camada 4 |
|-------|----------|
| Matriz A | AT-ACC-002/003 + holdout D-A |
| TC-01…08 | AT-ACC-005 + suite TC |
| TM-01…05 | AT-ACC-004 + suite TM |
| TC-09/10 | AT-ACC-006/007 |
| TC-A01/A02 | Habilitados por L3; revalidados no gate |
| TC-P01 | Pré-condição L2/L3 (não re-testar no gate) |

---

## Out of Scope

- Treino ou retreino de modelos (Camada 3 — escalar `gifi-simulation-engineer`)
- UI React / curvas Recharts (Camada 5 — `react-frontend-architect`)
- Alteração de limiares normativos (MAE 56, faixas) — change request via `gifi-domain-specialist`
- Elo 1b / Redes Neurais no release MVP
- MLflow Model Registry (Marco 2+ — ADR-003)
- Homologação substituída por julgamento ad hoc do stakeholder

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Normative | `A ∧ B ∧ C` não intercambiáveis | Parcial nunca libera produção |
| Normative | MAE ≤ 56 rígido | Sem relaxamento sem change request |
| Technical | Consumir L3 sem re-treinar | Gate = avaliação + inferência apenas |
| Technical | Cenários TC/TM versionados em YAML/JSON | Fixtures reproduzíveis |
| Resource | MVP local | Sem servidor de aceite remoto |
| Timeline | Habilitar UI demo antes de 31/08; prod só com gate | Report distingue modos |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `src/acceptance/` | Espelha `src/ingest/`, `src/simulation/` |
| **Config** | `config/acceptance.yaml` | MAE limit, paths, cenários TC/TM |
| **KB Domains** | `gifi-domain`, `ml-tabular`, `testing` | Matrizes, física, SHAP |
| **Deps novas** | `shap` (Matriz C RF), opcional | EN usa coef L3 |
| **IaC Impact** | None (Marco 1 local) | — |
| **Agente dono** | `gifi-acceptance-engineer` | Gate e release |
| **Agentes consultados** | `gifi-domain-specialist` (TC/TM), `gifi-simulation-engineer` (infer API) | Validação normativa |

---

## Data Contract

### Source Inventory

| Source | Type | Owner | Uso |
|--------|------|-------|-----|
| `models/candidates/{run_id}/` | joblib + JSON | Camada 3 | Candidato a avaliar |
| `data/l2/current.json` | Parquet + manifest | Camada 2 | Holdout + cenários |
| `docs/kb/gifi-domain/specs/` | YAML cenários | Camada 1 | Vetores TC/TM |
| `metrics_holdout.json` | JSON | L3 | Input Matriz A |

### Output Artifacts

| Artifact | Grain | Consumer |
|----------|-------|----------|
| `reports/acceptance/{run_id}/acceptance_report.json` | por candidato | UI, auditoria |
| `reports/acceptance/{run_id}/matriz_b_results.json` | por TC/TM | CD, stakeholder |
| `reports/acceptance/{run_id}/matriz_c_detractors.json` | por cenário | Camada 5 painel |
| `models/champion/{run_id}/` | cópia imutável | inferência produtiva |
| `models/current_champion.json` | pointer | Camada 5 bind |

### Gate Schema (normativo)

```json
{
  "run_id": "2026-07-10T08:08:31.339996Z",
  "l3_candidate_dir": "models/candidates/...",
  "l2_dataset_version": "2026-07-10T07:35:10Z",
  "matriz_a": { "ok": false, "mae_tsa_cascade": 94.79, "limit": 56.0 },
  "matriz_b": { "ok": false, "failures": ["TM-01"] },
  "matriz_c": { "ok": false, "scenarios": {} },
  "release_ok": false,
  "production_bind": false,
  "demo_mode": true,
  "generated_at": "ISO-8601"
}
```

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-ACC-01 | L3 exporta `feature_cols` e métricas suficientes para B/C | Gate precisa re-fit | [x] BUILD L3 |
| A-ACC-02 | Cenários TC/TM podem ser expressos como `infer_features` sintéticos | Redesign fixtures | [ ] |
| A-ACC-03 | SHAP disponível para RF; EN usa coeficientes | Fallback permutation_importance | [ ] |
| A-ACC-04 | Gap MAE atual é de modelagem, não de bug no gate | CD itera L3 | [x] smoke Excel |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Gap L3→release explícito |
| Users | 3 | CD, stakeholder, UI, L3 |
| Goals | 3 | MUST/SHOULD priorizados |
| Success | 3 | Métricas e flags mensuráveis |
| Scope | 3 | Out of scope fechado |
| **Total** | **15/15** | |

---

## Open Questions

| # | Question | Default para Design |
|---|----------|---------------------|
| 1 | SHAP obrigatório ou coef L3 + permutation para RF? | SHAP para RF; coef para EN (KB matriz-c-detractors) |
| 2 | Cenários TC em YAML em `config/acceptance_scenarios/` ou KB? | YAML em `config/` referenciando KB |
| 3 | Champion = mesmo run_id L3 ou seleção entre múltiplos runs? | Último `accept run` explícito; comparador multi-run = SHOULD Marco 2 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | define-agent | DEFINE inicial Camada 4 |

---

## Next Step

**Completed:** `/design` → [DESIGN_ACCEPTANCE_GATE.md](./DESIGN_ACCEPTANCE_GATE.md)

**Ready for:** `/build .claude/sdd/features/DESIGN_ACCEPTANCE_GATE.md`

**Agentes recomendados no Design:**

- **Owner:** `gifi-acceptance-engineer`
- **Consulta normativa:** `gifi-domain-specialist` (TC/TM, limiares)
- **Integração L3:** `gifi-simulation-engineer` (infer API, manifesto)
- **Bootstrap:** `python-developer` (CLI, package layout)

# DEFINE: Superfície de Uso Web (Camada 5 GIFI)

> Interface local homologável que consome template de cenário (Camada 1), validação online (Camada 2), inferência cascata (Camada 3) e política de release (Camada 4) — em **modo demonstração** até `release_ok=true`.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | WEB_UI |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (define-agent) |
| **Status** | Shipped |
| **Clarity Score** | 15/15 |
| **Source** | Acceptance Gate shipped (`.claude/sdd/archive/ACCEPTANCE_GATE/`), `docs/sketch/analytical-backbone.md` §Camada 5, PRD §5 |
| **Normative refs** | `docs/kb/gifi-domain/specs/template_cenario_v0.yaml`, `docs/kb/frontend-react/`, `docs/kb/ml-tabular/patterns/inference-serving.md`, `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` |

---

## Problem Statement

As Camadas 2–4 estão implementadas (`ingest`, `simulate`, `accept`), mas **não existe superfície de uso** para o stakeholder Veracel executar cenários Modo A/B, visualizar curvas de TSA/Carga/Extrativos e inspecionar top-3 detratores. Sem Camada 5, a homologação assistida até **31/08/2026** (Marco 2) fica limitada a CLIs e relatórios JSON.

**Estado atual:** `acceptance_report.json` retorna `demo_mode=true` e `release_ok=false` (MAE ~94–97). A UI **deve funcionar em modo demo** com candidato L3 explícito (`run_id`), exibindo banner de não-release, sem bind produtivo.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Stakeholder Veracel (Thiago)** | Homologação assistida | Precisa testar cenários sem linha de comando |
| **Planejamento / Abastecimento** | Consumidor eventual | Upload de planilha → curva TSA interpretável |
| **CD Keyrus** | Operador técnico | Demonstrar cascata + detratores em reuniões |
| **Camada 4 (Acceptance)** | Autoridade de release | UI não pode mascarar `demo_mode` |

**Decisor primário:** Stakeholder Veracel — aceita homologação em demo; release produtivo só com A∧B∧C.

**Fluxo de decisão (usuário):**

1. Operador seleciona **Modo A ou B** e faz upload da instância do template (`template_cenario_v0`).
2. Backend valida schema/mix/faixas (path online L2 — sem quarentena).
3. Backend carrega candidato L3 (`run_id` configurado ou último empacotado) e política L4 (`acceptance_report.json`).
4. Se `demo_mode=true` → inferência permitida com banner; se `demo=false` e `release_ok=false` → HTTP 403.
5. UI renderiza curvas (TSA, Carga, Extrativo) + top-3 detratores + warnings.
6. Usuário exporta snapshot (JSON/PDF leve) para evidência de homologação assistida.

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Upload CSV/XLSX conforme `template_cenario_v0` (Camada 1) |
| **MUST** | Seleção Modo A / Modo B por upload ou coluna `modo` |
| **MUST** | Exibir curvas/tabela: TSA/dia, Carga Alcalina, Extrativo_AT por linha/cenário |
| **MUST** | Painel top-3 detratores ΔTSA (Matriz C / explainability L3) |
| **MUST** | Respeitar `demo_mode` / `release_ok` do `acceptance_report.json` |
| **MUST** | Banner visível quando `demo_mode=true` (“não homologado para uso operacional”) |
| **MUST** | Rejeitar bind produtivo (`demo=false`) se `release_ok=false` |
| **SHOULD** | API HTTP local (FastAPI) encapsulando L2/L3/L4 — sem subprocess ad hoc na UI |
| **SHOULD** | Stack React+TS+Vite, Tailwind+Shadcn, RHF+Zod, TanStack Query, Recharts |
| **SHOULD** | Exibir metadados do modelo (`run_id`, campeões por elo, MAE holdout) |
| **SHOULD** | Download do resultado (JSON) e template oficial |
| **COULD** | Seletor de múltiplos `run_id` candidatos (comparador) |
| **COULD** | Export PDF do relatório de simulação |
| **COULD** | i18n PT-BR formal (strings externalizadas) |

---

## Success Criteria

- [ ] Upload de cenário válido Modo A retorna curvas + detratores em < 10s p95 (500 linhas)
- [ ] Upload inválido (mix ≠ 1, coluna ausente) retorna erro legível sem inferência
- [ ] Com `demo_mode=true`, simulação funciona e banner demo visível
- [ ] Com `release_ok=false` e `demo=false`, API retorna 403 com motivo
- [ ] Com `release_ok=true`, banner demo ausente e bind usa `models/champion/`
- [ ] Componentes presentacionais não contêm regras de MAE/faixas/Modo A
- [ ] Zod schema alinhado a `template_cenario_v0.yaml` (versionado)
- [ ] Testes Vitest+RTL cobrem upload happy path + erro de validação + banner demo

---

## Functional Requirements

| ID | Requirement | Component | Source |
|----|-------------|-----------|--------|
| FR-WUI-01 | Servir SPA Vite em dev; build estático servido pelo backend em prod local | Web shell | stack-and-structure.md |
| FR-WUI-02 | Endpoint `POST /api/scenario/validate` — validação leve online (I2) | Serving API | ingest-engine §1.1 |
| FR-WUI-03 | Endpoint `POST /api/simulate` — upload + Modo A/B → inferência cascata L3 | Serving API | inference-serving.md |
| FR-WUI-04 | Endpoint `GET /api/release-status` — lê `acceptance_report.json` + pointers L3/L4 | Serving API | acceptance reporter |
| FR-WUI-05 | Resposta inclui `curves[]`, `detractors[]` (max 3), `warnings[]`, `gate_ok`, `demo` | DTO | inference-serving.md |
| FR-WUI-06 | Carregar modelo por `run_id` query/config; prod usa `current_champion.json` | Model loader | artifact-packaging.md |
| FR-WUI-07 | Form upload com RHF + Zod espelhando template v0 | scenario-upload feature | schema-validation.md |
| FR-WUI-08 | Gráfico multi-série TSA / Carga / Extrativo (Recharts) | production-curves feature | production-curves-chart.md |
| FR-WUI-09 | Lista ordenada top-3 detratores com método (shap/coef/permutation) | detractors-panel | matriz-c-detractors.md |
| FR-WUI-10 | Header com badge Demo / Release + `run_id` + MAE holdout | layout | analytical-backbone §4 |
| FR-WUI-11 | Link/download template oficial (`template_cenario_v0`) | static assets | scenario-template-contract.md |
| FR-WUI-12 | Erros de ingest mapeados para mensagens PT-BR (`INGEST_*`) | error mapper | structured-logging.md |
| FR-WUI-13 | Modo B: aceitar colunas injetadas conforme template; Modo A: rejeitar injeção | validation | mode-a-b.md |
| FR-WUI-14 | Não executar treino/retreino na UI | policy | PRD §4.4 fora |

---

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-WUI-01 | Latência validação + inferência online (≤500 linhas) | p95 < 10s local |
| NFR-WUI-02 | Validação leve isolada | p95 < 3s (template SLA) |
| NFR-WUI-03 | TypeScript strict; sem `any` em DTOs públicos | ESLint + tsc |
| NFR-WUI-04 | Acessibilidade mínima | labels em forms, contraste Shadcn default |
| NFR-WUI-05 | Segurança MVP | localhost only; sem auth cloud |
| NFR-WUI-06 | Rastreabilidade | Resposta inclui `model_id`, `l2_dataset_version`, `acceptance_run_id` |

### NFR Acceptance Criteria

| NFR | Critério | Teste |
|-----|----------|-------|
| NFR-WUI-01 | p95 < 10s fixture 500 linhas | AT-UI-010 `@slow` |
| NFR-WUI-02 | validate-only < 3s | AT-UI-011 |
| NFR-WUI-03 | `npm run build` + `tsc --noEmit` | CI Marco 2 |

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-UI-001 | Upload Modo A válido | CSV fixture AT-006 | POST `/api/simulate` | 200 + curves + detractors |
| AT-UI-002 | Upload Modo B injeção | CSV com Extrativo injetado | POST `/api/simulate?mode=B` | 200; cascata usa injeção |
| AT-UI-003 | Modo A rejeita injeção | CSV Modo A com Extrativo | validate | 400 + motivo |
| AT-UI-004 | Mix inválido | soma mix ≠ 1 | validate | 400 `INGEST_MIX_SUM` |
| AT-UI-005 | Demo banner | `demo_mode=true` | render shell | Banner visível |
| AT-UI-006 | Prod blocked | `release_ok=false`, demo=false | POST simulate | 403 |
| AT-UI-007 | Prod allowed | `release_ok=true`, champion exists | POST simulate | 200; sem banner demo |
| AT-UI-008 | Detratores top-3 | cenário TC-09-like | simulate | ≤3 itens ordenados |
| AT-UI-009 | Metadados modelo | run_id configurado | GET release-status | MAE + campeões exibidos |
| AT-UI-010 | Performance 500 linhas | fixture grande | simulate ×20 | p95 < 10s |
| AT-UI-011 | Validate rápido | CSV 100 linhas | validate ×20 | p95 < 3s |
| AT-UI-012 | Template download | GET `/api/template` | download | arquivo v0 |
| AT-UI-013 | Erro arquivo | .txt upload | simulate | 415/400 |
| AT-UI-014 | Zod front/back parity | mesma linha inválida | validate UI + API | mesmo código erro |

**Mapeamento homologação oficial:**

| PRD / Casos | Camada 5 |
|-------------|----------|
| PRD §5 Upload + curvas | AT-UI-001/002 |
| PRD §5 Explicabilidade | AT-UI-008 |
| Modo A/B | AT-UI-002/003 |
| Demo vs release | AT-UI-005/006/007 |
| TC-P01 mix | AT-UI-004 |

---

## Out of Scope

- Retreino, feedback social, botões de “curtir” (PRD fora)
- Integração Databricks / Azure / cloud deploy
- RCA automática de desvios
- Caminho da Volta
- Alteração de limiares MAE/faixas na UI
- Elo 1b / NN na interface
- Autenticação SSO / multi-tenant
- Substituição do gate Camada 4 por julgamento visual

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Normative | Template schema owned by Camada 1 | UI importa versão; não redefine colunas |
| Normative | `demo_mode` quando `release_ok=false` | Banner obrigatório |
| Normative | Modo A não aceita injeção Extrativo/Carga | Validação antes inferência |
| Technical | Reutilizar APIs Python L2/L3/L4 | FastAPI chama módulos, não reimplementa cascata |
| Technical | Dual-path ingest: online ≠ batch | Sem quarentena no upload UI |
| Resource | MVP local (Mac/Windows dev) | Vite dev + uvicorn |
| Timeline | Homologável 31/08 em demo | Prod bind só pós-gate verde |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Frontend** | `web/` | Vite + React 18 + TS |
| **Backend** | `src/serving/` | FastAPI — novo pacote Python |
| **Config** | `config/serving.yaml` | `run_id`, paths L2/L4, host/port, demo default |
| **KB Domains** | `frontend-react`, `gifi-domain`, `ml-tabular` | UI + template + API |
| **Deps novas (Python)** | `fastapi`, `uvicorn`, `python-multipart` | Serving |
| **Deps novas (Node)** | ver `web/package.json` | React ecosystem |
| **IaC Impact** | None (Marco 2 local) | — |
| **Agente dono** | `react-frontend-architect` | UI + integração |
| **Agentes consultados** | `gifi-domain-specialist` (template), `gifi-simulation-engineer` (infer), `gifi-acceptance-engineer` (gate), `gifi-ingest-engineer` (validate online) | Fronteiras |

---

## Data Contract

### Source Inventory

| Source | Type | Owner | Uso |
|--------|------|-------|-----|
| Upload usuário | CSV/XLSX | Camada 5 | Instância cenário |
| `template_cenario_v0.yaml` | YAML | Camada 1 | Zod + validação |
| `data/l2/scenarios/{id}/` | Parquet/CSV | Camada 2 | Cenário publicado pós-validate |
| `models/candidates/{run_id}/` | joblib | Camada 3 | Inferência demo |
| `models/champion/` | joblib | Camada 4 | Inferência prod |
| `reports/acceptance/{run_id}/acceptance_report.json` | JSON | Camada 4 | demo_mode / release_ok |

### API Response (normativo)

```json
{
  "mode": "A",
  "demo": true,
  "gate_ok": false,
  "model_id": "2026-07-10T10:54:42.849161Z",
  "acceptance_run_id": "2026-07-10T10:54:42.849161Z",
  "l2_dataset_version": "2026-07-10T07:35:10Z",
  "curves": [
    {
      "label": "linha-1",
      "tsa_dia": 3420.5,
      "carga_alcalina": 19.2,
      "extrativo_at": 1.85
    }
  ],
  "detractors": [
    { "feature": "TPC", "delta_tsa": -120.3, "method": "shap" }
  ],
  "warnings": ["INGEST_PROXY_DB"],
  "metrics": { "mae_tsa_holdout": 96.7 }
}
```

### UI State (não persistir regras)

| State | Store | Notes |
|-------|-------|-------|
| Form upload | RHF local | — |
| Resultado simulação | TanStack Query cache | Invalidar por mode/run_id |
| release-status | TanStack Query | staleTime 60s |
| Sidebar/layout | React local ou URL | Zustand só se necessário |

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-WUI-01 | FastAPI pode importar `ingest`, `simulation`, `acceptance` no mesmo venv | Packaging ajuste | [x] monorepo atual |
| A-WUI-02 | Detratores por upload derivam de explainability L3 + SHAP on-the-fly | Latência ↑ | [ ] Design |
| A-WUI-03 | Stakeholder aceita demo com MAE > 56 até gate verde | Escopo UI ok | [x] backbone §4 |
| A-WUI-04 | Template v0 suficiente para Marco 2 | v1 change request | [x] D-E |
| A-WUI-05 | Operador configura `run_id` via env/config no MVP | UI picker = SHOULD | [ ] |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Gap L4→usuário explícito |
| Users | 3 | Stakeholder, CD, consumidor |
| Goals | 3 | MUST/SHOULD priorizados |
| Success | 3 | Mensurável (latência, demo, 403) |
| Scope | 3 | Out of scope fechado |
| **Total** | **15/15** | |

---

## Open Questions

| # | Question | Default para Design |
|---|----------|---------------------|
| 1 | Monorepo `web/` na raiz vs `src/web/`? | **`web/` na raiz** + `src/serving/` (padrão Vite) |
| 2 | Detratores: pré-computados L4 vs on-the-fly no simulate? | **On-the-fly** via L3 explainability + SHAP por request (cache Query) |
| 3 | Servir SPA: Vite proxy dev vs FastAPI StaticFiles prod? | **Dev:** Vite proxy `/api` → uvicorn; **Prod local:** FastAPI monta `web/dist` |
| 4 | `run_id` default quando não configurado? | **`config/serving.yaml`** `default_run_id`; UI mostra aviso se ausente |
| 5 | Vitest e2e com Playwright no MVP? | **RTL + MSW** no BUILD; Playwright COULD Marco 2 |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-10 | define-agent | DEFINE inicial Camada 5 |
| 1.1 | 2026-07-10 | ship-agent | Shipped and archived |

---

## Next Step

```bash
/design .claude/sdd/features/DEFINE_WEB_UI.md
```

**Agentes recomendados no Design:**

- **Owner:** `react-frontend-architect`
- **API bridge:** `python-developer` + `gifi-simulation-engineer`
- **Template / Modo A/B:** `gifi-domain-specialist`
- **Gate / demo policy:** `gifi-acceptance-engineer`
- **Validate online:** `gifi-ingest-engineer`

**Pré-requisitos satisfeitos:**

- Camada 2 shipped (`ingest scenario-validate|publish`)
- Camada 3 shipped (`simulate infer --run-id`)
- Camada 4 shipped (`accept run`, `acceptance_report.json` com `demo_mode`)

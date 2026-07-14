# DEFINE: Predict-TSA Analytics

> Estender `POST /api/predict-tsa` (opt-in) com curva de sensibilidade e top-3 por ablação local, e exibir ambos na aba What-if — sem usar `/api/simulate` nem `/api/forecast`.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PREDICT_TSA_ANALYTICS |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio |
| **Status** | ✅ Shipped |
| **Clarity Score** | 15/15 |
| **Source** | `.claude/sdd/features/BRAINSTORM_PREDICT_TSA_ANALYTICS.md` (Approach A confirmada) |

---

## Problem Statement

A aba What-if (Produto B) só devolve um `tsa_dia` pontual via `/api/predict-tsa`. Analistas e a demo de homologação (até 31/08, gate A∧B∧C ainda não verde) precisam ver **como a TSA reage** a uma variável de processo e **quais features mais puxam** o cenário — sem depender do cascata (`/api/simulate`) nem do forecast com histórico (`/api/forecast`), e sem empurrar regra de negócio para o React.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Cientista / engenheiro de dados | Opera what-if e valida premissa física | Só vê um número; não vê curva nem ranking de impacto no mesmo request |
| Stakeholder Veracel (demo) | Homologação assistida Camada 5 | Precisa superfície analítica sem Matriz C oficial nem upload de planilha |
| Frontend (Camada 5) | Mantém What-if | Não pode calcular sweeps/Δ no browser (contrato + a11y + SSOT de faixa) |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Opt-in no mesmo `POST /api/predict-tsa`: default sem analytics = contrato atual (retrocompatível) |
| **MUST** | Com analytics: retornar `sensitivity[]` (sweep 1 variável em faixa oficial) + `detractors` top-3 (`method: local_ablation`) |
| **MUST** | Baseline = cenário do request após `resolve_process_fields` (Tier A/B) |
| **MUST** | Cálculo 100% no serving; UI What-if apenas renderiza |
| **MUST** | Disclaimer explícito: não é Matriz C / não libera gate L4 |
| **MUST** | Pytest (shape + faixa) + Vitest smoke no painel; dicionário API + CHANGELOG |
| **SHOULD** | Seletor de `sensitivity_variable` na UI (whitelist); default `db_sgf` |
| **SHOULD** | p95 local com analytics default (15 steps + ablações) **≤ 2,0 s** |
| **COULD** | Reusar visualmente `CurvesChart` / `DetractorsPanel` com DTO adaptado (sem acoplar ao schema de `/simulate`) |
| **COULD** | Persistir blocos analytics no audit SQLite quando presentes (sem mudança de schema se JSON response já for gravado) |

---

## Success Criteria

- [ ] Omitting `include_analytics` or `false`: response **sem** chaves `sensitivity` / `detractors` (ou ambas `null` — Design escolhe **uma** convenção e documenta); demais campos idênticos ao contrato v1.1 atual
- [ ] `include_analytics=true`: `sensitivity` tem comprimento = `sensitivity_steps` (default **15**); extremos cobrem **low e high inclusivos** da faixa oficial da variável
- [ ] Default `sensitivity_variable=db_sgf` com faixa API **[465, 515]** kg/m³
- [ ] `detractors` tem **exatamente 3** itens, ordenados por `|delta_tsa|` desc; cada item: `feature`, `delta_tsa`, `method="local_ablation"`
- [ ] `sensitivity_variable` fora da whitelist ou `sensitivity_steps` fora de **[5, 31]** → HTTP **422**
- [ ] UI What-if com analytics: exibe gráfico da série + lista top-3; **zero** cálculo de sweep/Δ no cliente
- [ ] Texto de disclaimer visível (API e UI) distinguindo de Matriz C / aceite L4
- [ ] `docs/api/DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md` + `docs/CHANGELOG.md` atualizados
- [ ] ≥ 3 testes pytest novos/estendidos + ≥ 1 Vitest smoke passando

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-PTA-001 | Retrocompat | Serving + `sample_process_payload` | `POST /api/predict-tsa` **sem** query analytics | 200; `product=what_if_direct`; **ausência** de `sensitivity`/`detractors` (convenção escolhida); `tsa_dia` numérico |
| AT-PTA-002 | Analytics happy path | Mesmo payload | `POST ...?include_analytics=true` | 200; `len(sensitivity)==15`; `sensitivity[0].value==465` e último `==515` (db_sgf); `len(detractors)==3`; `method=local_ablation` |
| AT-PTA-003 | Variável custom | Payload válido | `include_analytics=true&sensitivity_variable=carga_alcalina&sensitivity_steps=11` | 200; 11 pontos; extremos **17,5** e **21,0** |
| AT-PTA-004 | Steps inválidos | Payload válido | `sensitivity_steps=4` ou `32` com analytics | **422** |
| AT-PTA-005 | Variável inválida | Payload válido | `sensitivity_variable=foo` | **422** |
| AT-PTA-006 | Determinismo | Mesmo payload + analytics | 2 POSTs idênticos | `tsa_dia`, `sensitivity`, `detractors` bit-a-bit iguais (float tol ≤ 1e-6) |
| AT-PTA-007 | UI smoke | MSW/mock com sensitivity+detractors | Abrir aba What-if, submit com analytics | Curva renderiza; top-3 listado; sem chamar `/api/simulate` nem `/api/forecast` |
| AT-PTA-008 | Disclaimer | Response com analytics | Ler `disclaimer` (e UI) | Contém menção a explicabilidade assistida / **não** Matriz C (ou equivalente PT-BR documentado) |

---

## Functional Requirements (extraídos do BRAINSTORM)

| ID | Requirement |
|----|-------------|
| FR-PTA-01 | Query params no POST: `include_analytics` (bool, default false), `sensitivity_variable` (str, default `db_sgf`), `sensitivity_steps` (int, default 15, clamp/validação [5, 31]) |
| FR-PTA-02 | Corpo JSON permanece `PredictTsaRequest` / `ProcessVariablesInput` (sem segundo baseline no body) |
| FR-PTA-03 | Sweep: mantém features resolvidas fixas; varia só `sensitivity_variable` em grid linear inclusivo min→max da faixa oficial API/SSOT |
| FR-PTA-04 | Ablação local: para cada feature do **pool elegível** (Design define whitelist contínua), substituir valor pela **âncora de ablação** (default: ponto médio da faixa oficial quando bilateral; regras unilaterais/`idade`/`prod_alcali_class`/`vmi_*` documentadas no DESIGN), predicinar, `delta_tsa = tsa_ablated - tsa_dia`; rankear por `|delta_tsa|`; top-3 |
| FR-PTA-05 | Whitelist mínima de variáveis de sensibilidade: `db_sgf`, `carga_alcalina`, `kappa`, `casca_pct`, `tpc`, `extrativo_at`, `idade` (faixas/estratégia de extremos no DESIGN a partir de Pydantic + `operational-ranges.yaml`) |
| FR-PTA-06 | Não alterar rotas `/api/forecast*` nem `/api/simulate` / scenario |
| FR-PTA-07 | Não ler Parquet L2 na UI; só `current_tsa` + resolve já existente |
| FR-PTA-08 | Tipos TS + painel What-if atualizados; Forecast/Cenário intactos |

---

## Out of Scope

- Endpoints separados `/sensitivity` ou `/detractors`
- Contribuição por coeficientes Lasso crus
- Curvas Elo 1→2→3 / séries Carga / Extrativo (cascata)
- Batch multi-linha ou upload de planilha em predict-tsa
- Baseline operacional fixa (mediana holdout) ou segundo formulário de referência
- Remover ou esconder abas Forecast / Cenário
- Intervalo `tsa_dia_lo` / `tsa_dia_hi` no what-if
- Tratar top-3 local como Matriz C ou pré-condição de `release_ok`
- Auth / rate limit do serving (débito já documentado)
- Fechar débitos P0/P1 do Ingest (`GAP_INGEST_ENGINE_FONTES.md`) nesta feature

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | Python 3.12 + FastAPI + Pipeline joblib existentes | Extensão de `run_predict_tsa` / schemas |
| Technical | UI: React + TanStack Query + Recharts; **sem regra de negócio no JSX** | DTO pronto do backend |
| Domain | Faixas oficiais SSOT (`ProcessVariablesInput` + `docs/kb/gifi-domain/specs/operational-ranges.yaml`) | Sweep/ablações não inventam faixas no FE |
| Product | Demo / homologação; gate A∧B∧C independente | Disclaimer obrigatório |
| Performance | Até ~13 + 31 predicts/request no pior caso | Validar teto de steps; meta SHOULD ≤ 2 s local |
| Docs | PT-BR; autor/data; CHANGELOG | Obrigatório no ship da feature |
| Architecture | Ingest já publicado; binding via `current_tsa.json` | Sem novo path I4 na UI |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `src/serving/services/` (novo helper analytics), `src/serving/schemas.py`, `src/serving/routes/predict_tsa.py`, `web/src/features/what-if-direct/`, `web/src/types/predictTsa.ts` | Espelha padrão L5 |
| **Tests** | `tests/serving/test_predict_tsa.py` (+ novo se necessário), Vitest sob `what-if-direct` ou painel compartilhado | Fixture `sample_process_payload` |
| **Docs** | `docs/api/DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md`, `docs/CHANGELOG.md` | Contrato response |
| **KB Domains** | `frontend-react`, `gifi-domain`, `ml-tabular` (artefato TSA) | Patterns: no-business-in-ui; faixas; packaging |
| **IaC Impact** | None | Sem mudança de hosting |

---

## Data Contract

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| Body `ProcessVariablesInput` | JSON API | 1 linha/request | Tempo real | UI / cliente |
| `models/primeira_base/current_tsa.json` + `.joblib` | Artefato L3 | <1 MB | Até rebind | Simulation / serving |
| Resolve Tier A/B | Serviço serving | 1×/request | Tempo real | `resolve_process_fields` |

### Schema Contract — response analytics (quando ligado)

| Campo | Tipo | Constraints | PII? |
|-------|------|-------------|------|
| `sensitivity` | `array[{ value: float, tsa_dia: float }]` | len ∈ [5, 31]; ordenado por `value` asc | Não |
| `sensitivity_variable` | string (eco) | Whitelist FR-PTA-05 | Não |
| `sensitivity_steps` | int (eco) | 5–31 | Não |
| `detractors` | `array[{ feature: string, delta_tsa: float, method: "local_ablation" }]` | **len = 3**; sorted \|Δ\| desc | Não |
| `disclaimer` | string | Deve distinguir de Matriz C quando analytics on | Não |

### Freshness SLAs

| Layer | Target | Measurement |
|-------|--------|-------------|
| Predição + analytics | Resposta síncrona no mesmo request | Latência HTTP; meta SHOULD ≤ 2 s p95 local |

### Completeness Metrics

- Com `include_analytics=true` e 200: `sensitivity` e `detractors` sempre presentes e bem formados
- Com analytics off: resposta sem blocos analytics (convenção única)

### Lineage Requirements

- Cada ponto de `sensitivity` e cada `delta_tsa` rastreável ao mesmo `model_id` / `family` da predição principal
- Audit SQLite (se ativo) continua gravando `response_json` completo incluindo analytics

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Ablação por âncora de faixa (ponto médio / regra Design) produz ranking útil na demo | Pode precisar de stress às bordas (COULD pós-MVP) | [x] Confirmado conceito no BRAINSTORM; detalhe no DESIGN |
| A-002 | Artefato atual (`current_tsa`) aceita DataFrame de 1 linha repetido N vezes sem drift | Pipeline quebrado → feature bloqueada | [x] Já usado em `run_predict_tsa` |
| A-003 | Whitelist de 7 variáveis cobre demo stakeholder | Se pedirem mix `%` como eixo, estender whitelist | [ ] Confirmar no DESIGN com domínio |
| A-004 | Response JSON opcionalmente maior (~15+3 objetos) cabe no audit atual | Sem migração | [x] Audit grava response inteiro |
| A-005 | Query params em POST são aceitáveis no proxy Vite / clientes | Se não, mover flags para body wrapper — mudança mínima | [ ] Validar no DESIGN/build |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Escopo, impacto e APIs excluídas explícitos |
| Users | 3 | CD, stakeholder demo, FE com dores distintas |
| Goals | 3 | MUST/SHOULD/COULD priorizados |
| Success | 3 | Números (15 steps, faixa 465–515, top-3, 422, ≤2 s, contagem testes) |
| Scope | 3 | Out of scope alinhado ao YAGNI do BRAINSTORM |
| **Total** | **15/15** | Gate ≥12 satisfeito |

---

## Open Questions

Resolvidos no DESIGN (não bloqueiam DEFINE):

1. Convenção exacta sem analytics: **omitir** chaves vs `null` (escolher uma).
2. Algoritmo fechado de ablação para features unilaterais (`tpc≥45`, `casca≤1.5`), `idade`, `prod_alcali_class` e `vmi_*` (no/out do pool).
3. Labels PT-BR dos feature names na UI (map API → label humano).

**None blocking — ready for Design.**

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-13 | Emerson Antônio (define-agent) | Extraído de BRAINSTORM Approach A |
| 1.1 | 2026-07-14 | ship-agent | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_PREDICT_TSA_ANALYTICS.md`

Agentes sugeridos: design → `react-frontend-architect` + padrões serving existentes; faixas → `gifi-domain-specialist` se ambíguo.

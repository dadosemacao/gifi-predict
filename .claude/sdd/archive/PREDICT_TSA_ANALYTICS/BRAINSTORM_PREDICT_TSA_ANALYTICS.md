# BRAINSTORM: Predict-TSA Analytics

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | PREDICT_TSA_ANALYTICS |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio (brainstorm-agent) |
| **Status** | ✅ Shipped |

---

## Initial Idea

**Raw Input:** Analisar fontes e o plano `docs/sketch/analytical-backbone.md`, identificar onde paramos e o próximo passo. Alinhar com o que o Ingest Engine já entrega. Trabalhar Analytics **apenas** com a API `/api/predict-tsa` — o que precisa mudar?

**Context Gathered:**
- Backbone Camadas 1–5 implementadas (v0.4.x); gate A∧B∧C ainda não verde (UI em demo).
- Gaps UX da Camada 5 (Zod, demo/prod, field_origins/warnings, Vitest, docs segurança) **fechados**.
- Ingest Marco 1 **shipped**; débitos em `docs/analysis/GAP_INGEST_ENGINE_FONTES.md` não bloqueiam Analytics (não leem Parquet L2 na UI).
- SPA tem 3 produtos: Cenário (`/api/simulate`), Forecast (`/api/forecast`), What-if (`/api/predict-tsa`).
- `POST /api/predict-tsa` hoje devolve só `tsa_dia` pontual + origins/warnings/metrics — sem série nem top-3.
- PRD §5 pede curvas + top-3; isso hoje depende do cascata/`simulate`. Decisão de produto: **estender predict-tsa** para analytics assistida, sem reabrir `/simulate`/`/forecast` nesta onda.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `src/serving/services/`, `src/serving/schemas.py`, `web/src/features/what-if-direct/` | Backend computes analytics; UI only renders |
| Relevant KB Domains | `frontend-react`, `gifi-domain` (faixas), `ml-tabular` (artefato TSA) | Faixas SSOT; sem regra de negócio no JSX |
| IaC Patterns | N/A (local serving) | Sem mudança de infra nesta onda |
| Samples | `tests/serving/conftest.py` → `sample_process_payload` (1ª linha `base/primeira_base.csv`); `tests/serving/test_predict_tsa.py` | Reusar como fixture de analytics |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Escopo vs outras APIs? | **(c)** Estender `/api/predict-tsa` para charts/explicabilidade; sem `/simulate` nem `/forecast` | Novo contrato no Produto B |
| 2 | Payload analítico MVP? | **(d)** Sensibilidade (curva) + top-3 linear/local | Dois blocos na response |
| 3 | Baseline de ΔTSA / sweep? | **(a)** Cenário do próprio request | Sem baseline operacional fixa nem 2º formulário |
| 4 | Amostras para grounding? | **(a)** Requests/responses reais / fixtures de teste | Fixtures existentes bastam para /define |

**Minimum Questions:** 3 (atendido) + amostra

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | `tests/serving/conftest.py` (`sample_process_payload`) | 1 payload completo | Origem: `base/primeira_base.csv` iloc[0] |
| Output examples | `tests/serving/test_predict_tsa.py` | Asserts product/status | Sem analytics ainda — estender nos testes |
| Ground truth | Artefato `models/primeira_base/current_tsa.json` + pipeline | 1 bind | Predições determinísticas para asserts |
| Related code | `src/serving/services/predict_tsa.py`, `WhatIfDirectPanel.tsx`, Recharts/DetractorsPanel | — | Ponto de extensão e reuso de UI |

**How samples will be used:**
- Fixture pytest para `include_analytics=true` (shape de `sensitivity` / `detractors`)
- Smoke Vitest com response mockada na aba What-if
- Validação de faixas de sweep contra SSOT / Pydantic

---

## Approaches Explored

### Approach A: Enriquecer o mesmo `POST /api/predict-tsa` (opt-in) ⭐ Recommended

**Description:** Flag `include_analytics` (+ `sensitivity_variable` / `sensitivity_steps`). Com analytics off, contrato atual intacto. Com on: servidor calcula sweep (1 variável, faixa oficial) e top-3 por ablação local (|ΔTSA| vs `tsa_dia` do request), model-agnostic via `pipe.predict` repetido.

**Pros:**
- Um endpoint; FE What-if já integrado
- Independente da família do modelo (Lasso hoje, outra depois)
- Alinhado ao Ingest já entregue (só `current_tsa`)

**Cons:**
- N+1 predicções por request (aceitável para N≈13 + ~15 steps)
- Explicabilidade **não** é Matriz C do gate L4 — precisa disclaimer

**Why Recommended:** Confirma C+D+baseline A com YAGNI e menor superfície de API.

---

### Approach B: Endpoints novos (`/sensitivity`, `/detractors`)

**Description:** Separar analytics em rotas dedicadas.

**Pros:** Separação de contratos; cache por rota.  
**Cons:** Mais tipos, docs e round-trips no FE sem ganho nesta onda.

---

### Approach C: Loops no browser sobre `predict-tsa` atual

**Description:** FE dispara dezenas de POSTs e monta curva/top-3.

**Pros:** Zero mudança de schema.  
**Cons:** Regra de negócio na UI; faixas duplicadas; latência/erros. Rejeitado.

---

## Data Engineering Context (if applicable)

### Source Systems
| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|-------------------|
| Request JSON processo (13 features resolvidas) | API online | 1 linha/request | Tempo real (user) |
| `current_tsa.json` + `.joblib` | Artefato Camada 3 | <1 MB | Bind estático até rebind |

### Data Flow Sketch
```text
[UI What-if] → POST /api/predict-tsa?include_analytics=true
                    → resolve_process_fields (Tier A/B)
                    → predict tsa_dia
                    → sweep variável (faixa SSOT) → sensitivity[]
                    → ablação local 13 features → detractors[top-3]
                    → PredictTsaResponse enriquecida
[UI] → Recharts (sensitivity) + lista top-3 (adaptada)
```

### Key Data Questions Explored
| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Precisa Parquet L2 na UI? | Não | Só artefato TSA + request |
| 2 | Batch multi-linha? | Fora do MVP | YAGNI |
| 3 | Consumidor? | Analista / demo What-if | Camada 5 aba whatif |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A |
| **User Confirmation** | 2026-07-13 (validações 1 e 2: sim) |
| **Reasoning** | Opt-in no mesmo POST; sensibilidade + top-3 local; baseline = request; UI só What-if |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | Analytics só via `/api/predict-tsa` | Foco produto B; Ingest já ok | Usar `/simulate` ou `/forecast` |
| 2 | Payload = curva + top-3 | Demo “impacto + o que puxa TSA” | Só um dos dois; batch N linhas |
| 3 | Baseline = request | Zero config; what-if atual | Mediana holdout / 2º formulário |
| 4 | Cálculo no serving (ablation + sweep) | UI sem regra de negócio; model-agnostic | Coeficientes Lasso crus; loops no FE |
| 5 | Opt-in `include_analytics` | Compatibilidade retroativa | Sempre calcular (custo desnecessário) |
| 6 | Forecast/Cenário intactos | Fora do pedido desta onda | Simplificar SPA removendo abas |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Endpoints analytics separados | Overkill vs opt-in no POST | Yes |
| Contribuição via coeficientes Lasso | Família pode mudar; ablação basta | Yes (se família linear fixa) |
| Curvas Elo 1→2→3 / Carga / Extrativo | Exigem cascata `/simulate` | Yes (outra feature) |
| Batch N linhas / upload planilha no predict-tsa | Escopo pontual + analytics | Yes |
| Baseline operacional fixa no servidor | Usuário escolheu baseline request | Yes |
| Esconder Forecast/Cenário | Não pedido | Yes |
| Intervalo lo/hi no what-if | Modelo direto sem cobertura | Maybe |
| Igualar top-3 a Matriz C L4 | Gate distinto; disclaimer obrigatório | No (contratos diferentes) |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Architecture concept (Approach A) | ✅ | sim | No |
| Contract + UI breakdown | ✅ | sim | No |

**Minimum Validations:** 2 (atendido)

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)
A aba What-if (`/api/predict-tsa`) só exibe TSA pontual; para Analytics de demo/homologação precisamos de curva de sensibilidade e top-3 de impacto sem depender de `/api/simulate` nem `/api/forecast`, reusando o artefato e o resolve de processo já alinhados ao Ingest/Camada 3.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Analista / CD | Quer ver como TSA reage a uma variável e o que mais “puxa” o cenário |
| Stakeholder demo até 31/08 | Precisa superfície analítica sem gate A∧B∧C verde nem cascata completa |

### Success Criteria (Draft)
- [ ] `include_analytics=false` (default): response idêntica ao contrato atual
- [ ] `include_analytics=true`: retorna `sensitivity[]` e `detractors` top-3 com `method: local_ablation`
- [ ] Sweep usa faixa oficial SSOT da variável escolhida; demais features = request resolvido
- [ ] UI What-if renderiza curva + top-3 sem calcular Δ/sweep no cliente
- [ ] Disclaimer explícito: não substitui Matriz C / aceite L4
- [ ] Pytest + Vitest cobrindo shape e smoke UI
- [ ] Dicionário API + CHANGELOG atualizados

### Constraints Identified
- Não alterar contratos de `/api/forecast` nem `/api/simulate` nesta feature
- Não ler artefatos Parquet L2 na UI
- Faixas de sweep = SSOT de domínio / Pydantic (não hardcode divergente no FE)
- Performance: sweeps limitados (`sensitivity_steps` com teto razoável)

### Out of Scope (Confirmed)
- Matriz C oficial / bind produtivo por esta explicabilidade
- Remoção das abas Forecast e Cenário
- Extensão de API para multi-linha / upload
- Autenticação serving (débito já documentado)

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 4 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 8 |
| Validations Completed | 2 |
| Duration | ~1 sessão |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_PREDICT_TSA_ANALYTICS.md`

Agentes sugeridos no /define → /design → /build: `react-frontend-architect` (UI), domínio faixas via `gifi-domain-specialist` se ambíguo, serving Python alinhado a `python-developer` / padrão existente em `src/serving/`.

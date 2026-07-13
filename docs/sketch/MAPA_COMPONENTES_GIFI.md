# Mapa de Componentes e Dependências — Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.2  
**Base normativa:** `PRD_GIFI_v1.1.md`, `RESUMO_TECNICO_GIFI_v1.1.md`, `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`  
**Objetivo:** visão única para decompor o sistema em tarefas de construção.

---

## 1. Visão em uma frase

O GIFI é um **simulador preditivo em cascata** (Caminho da Ida): dados de planejamento florestal → features de mix/qualidade → Elo 1 (Extrativos) → Elo 2 (Carga) → Elo 3 (TSA/dia) → interface + explicabilidade, validado por três matrizes de aceite (MAE, física, detratores).

---

## 2. Mapa de camadas

### 2.1 Visão de produto (componentes C0–C9)

```
L0  Fundação documental + base bruta
L1  Dados limpos + engenharia de features
L2  Cascata preditiva (Elo 1 → 1b → 2 → 3)
L3  Validação e seleção de modelo (Matrizes A/B/C)
L4  Produto (interface + relatório de desvios)
```

Diagrama: `graphics/mapa_componentes_gifi.png`

### 2.2 Mapeamento para backbone + código (2026-07-13)

| Backbone | Pacote / CLI | Componentes C* | Status |
|----------|--------------|----------------|--------|
| Camada 1 — Domínio | `docs/kb/gifi-domain/` | C0 | **Pronto** |
| Camada 2 — Ingest | `src/ingest/` · `ingest` | C1 + C2 | **Shipped** |
| Camada 3 — Simulação | `src/simulation/` · `simulate` | C3 + C4 + C5 | **Shipped** |
| Camada 4 — Aceite | `src/acceptance/` · `accept` | C6 (+ C7 parcial) | **Shipped (MVP)** |
| Camada 5 — Serving + UI | `src/serving/` · `serve` + `web/` | C8 (+ C7 parcial) | **Shipped (demo)** |
| Marco 4 | (a construir) | C9 | **Pendente** |
| Fora MVP | — | C3b, NN | **NO-GO / opcional** |

Referências SDD arquivadas: `.claude/sdd/archive/{INGEST_ENGINE,SIMULATION_ENGINE,ACCEPTANCE_GATE,WEB_UI,SERVING_SQLITE_AUDIT}/`

---

## 3. Componentes principais

### C0 — Fundação documental

| Item | Conteúdo |
|---|---|
| **O que é** | PRD, Resumo, Casos de Teste, Faixas Operacionais |
| **Entrega** | Contratos de escopo, faixas, KPIs, protocolo de homologação |
| **Depende de** | — (já consolidado na v1.1) |
| **Bloqueia** | Qualquer implementação sem referência numérica |
| **Status** | **Pronto** |

---

### C1 — Ingestão e limpeza de dados

| Item | Conteúdo |
|---|---|
| **O que é** | Pipeline que lê a base QM×Processo, tipa colunas, aplica filtros e imputações |
| **Regras-chave** | Unidade kg/m³; filtro TSA < 1.000; `DB_LAB = 0,985 × DB_SGF` se Lab ausente; soma mix ≈ 1,0 |
| **Entradas** | Excel consolidado 2018–2025 (+ tabelas limpas da TI, quando disponíveis) |
| **Saídas** | Parquet L2 versionado (`data/l2/`), manifesto, pointer `current.json` |
| **Implementação** | `src/ingest/` — I1 conectores, I2 validação, I3 transformação, I4 publicação, I5 sinais |
| **CLI** | `ingest batch`, `scenario-validate`, `scenario-publish`, `reprocess` |
| **Depende de** | C0 (faixas/schema) |
| **Bloqueia** | C2…C6 |
| **Status** | **Concluído (Camada 2)** — shipped 2026-07-10; débito Marco 2: AT-011/012/017 E2E dedicados |

---

### C2 — Engenharia de features (Mix A/B/C + qualidade)

| Item | Conteúdo |
|---|---|
| **O que é** | Camada analítica: percentuais, compostos, diversidade, médias ponderadas |
| **Features** | `pct_*`, `pct_ABC`, `pct_CDMG`, `mix_entropy`, `mix_hhi`, `dom_X`, DB/Extrativos/Casca ponderados, VMI, TPC, Volume, Kappa |
| **Implementação** | Integrado ao Ingest I3 (`feature-columns.yaml`, agregação turno→dia D-C) |
| **Depende de** | C1 |
| **Bloqueia** | C3, C4, C5, C6 |
| **Testes associados** | TC-08, TC-P01, TC-A02 (parcialmente cobertos em `tests/ingest/`) |
| **Status** | **Concluído (integrado ao Ingest)** — qualidade de dados documentada em `docs/analysis/RELATORIO_DADOS_ENGENHARIA_VARIAVEIS.md` |

---

### C3 — Elo 1: Extrativo Álcool-Toluol

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo que estima Extrativo_AT a partir de Sítio + Idade (+ mix) |
| **Saída** | `Extrativo_AT` estimado |
| **Implementação** | `src/simulation/models/` + cascata Modo A/B |
| **Depende de** | C2 |
| **Bloqueia** | C5 (Elo 2), parcialmente C6 |
| **Métrica** | `MAE_Extrativos` (reportar; não bloqueia sozinho o aceite global) |
| **Risco** | Cobertura Lab forte só a partir de ~2024 |
| **Status** | **Concluído (Camada 3)** — MAE reportado no holdout; gate global ainda falha |

---

### C3b — Elo 1b: % Casca (opcional MVP+)

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo auxiliar Sítio + Idade → % Casca |
| **Depende de** | C2 |
| **Bloqueia** | Explicabilidade com casca; não bloqueia MVP mínimo do Elo 3 se Casca medida existir |
| **Decisão** | **NO-GO no MVP** (D-B confirmada 2026-07-09); Casca só como feature quando medida |
| **Status** | **Fora do escopo MVP** — go/no-go pós-31/08 |

---

### C4 — Elo 2: Carga Alcalina

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo Extrativo_AT + TPC + DB_SGF → Carga Alcalina |
| **Implementação** | `src/simulation/` — estágio elo2 da cascata |
| **Depende de** | C2 + C3 (no Modo A); no Modo B aceita Extrativo injetado |
| **Bloqueia** | C5 (Elo 3 no Modo A) |
| **Métrica** | `MAE_Carga` |
| **Status** | **Concluído (Camada 3)** |

---

### C5 — Elo 3: TSA/dia (modelo campeão)

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo final de produção: mix + qualidade + processo → TSA/dia |
| **Algoritmos** | Baseline → ElasticNet → RF (+ XGB/LGBM/CatBoost, OOF stack) |
| **Implementação** | `src/simulation/` — treino, evaluate, infer; candidatos em `models/candidates/{run_id}/` |
| **Depende de** | C2 + C4 (+ C3 no Modo A) |
| **Bloqueia** | C6, C7, C8 |
| **KPI** | `MAE_TSA ≤ 56` + monotonicidade física |
| **Status** | **Concluído (engenharia)** — melhor holdout ~94–97 (`release_ok=false`); ver `docs/analysis/DIAGNOSTICO_MAE_ELO3.md` |

---

### C6 — Validação e seleção (Matrizes A/B/C)

| Item | Conteúdo |
|---|---|
| **O que é** | Protocolo de aceite e escolha do modelo campeão |
| **Matriz A** | Holdout temporal; MAE ≤ 56 |
| **Matriz B** | TC-01…08 + TM-01…05 (física) — **MVP:** TC-03/05 + TM-01…05 |
| **Matriz C** | TC-09/10 (top-3 detratores) |
| **Implementação** | `src/acceptance/` — `accept run|report`; relatório em `reports/acceptance/{run_id}/` |
| **Depende de** | C3, C4, C5 (+ artefatos de explicabilidade L3) |
| **Bloqueia** | Release produtivo da interface (bind campeão) |
| **Status** | **Concluído (MVP Camada 4)** — gate A∧B∧C verde pendente de modelagem; `demo_mode=true` no Excel atual |

---

### C7 — Explicabilidade e gestão de desvios

| Item | Conteúdo |
|---|---|
| **O que é** | Decomposição de impacto (SHAP/importância) → top-3 detratores |
| **Implementação parcial** | L3: `extract_explainability` no manifesto; L4: Matriz C (SHAP/coef/permutation) |
| **Depende de** | C5 (modelo campeão/candidato) |
| **Bloqueia** | Matriz C completa na homologação; painel da UI |
| **Fora** | RCA automática |
| **Status** | **Parcial** — motor pronto; UI e relatório Marco 4 pendentes |

---

### C8 — Interface web do simulador

| Item | Conteúdo |
|---|---|
| **O que é** | SPA React + FastAPI serving: upload cenário Modo A/B, forecast operacional, what-if direto |
| **Depende de** | C5 + C6 (mínimo funcional demo) + C7 (homologação completa) |
| **Implementação** | `src/serving/` (API) + `web/src/` (React/Vite); CLI `serve run` |
| **Endpoints** | `/api/simulate`, `/api/scenario/validate`, `/api/forecast`, `/api/predict-tsa`, `/api/release-status` |
| **Integração** | `acceptance_report.json` (`demo_mode`), champion L3/L4, audit SQLite |
| **Prazo homologação** | **31/08/2026** (modo demo enquanto `release_ok=false`) |
| **Fora** | Retreino na UI, cloud, Caminho da Volta |
| **Status** | **Shipped (MVP demo)** — shipped 2026-07-10; extensões forecast/audit 2026-07-13 |

---

### C9 — Relatório de aderência e encerramento

| Item | Conteúdo |
|---|---|
| **O que é** | Documentação de métricas, estresse físico, limitações, versão do modelo |
| **Depende de** | C6 + C7 + C8 |
| **Prazo** | Marco 4 (até 03/11/2026) |
| **Status** | **Pendente** |

---

## 4. Grafo de dependências (ordem lógica)

```
C0 Docs ──┐
          ├──► C1 Limpeza ──► C2 Features ──┬──► C3 Elo1 ──► C4 Elo2 ──┐
C_raw ────┘         [L2 ingest]            ├──► C3b (NO-GO MVP) ───────┼──► C5 Elo3 [L3 simulate]
                                            └─────────────────────────┘
                                                      │
                                                      ▼
                                              C6 Validação A/B/C [L4 accept]
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                                 C7 Explain        C8 UI [L5]        (release)
                                    └────────┬────────┘
                                             ▼
                                          C9 Relatório
```

**Regra:** não homologar C8 produtivo sem `release_ok=true`; modo demo permitido com `demo_mode=true`.

---

## 5. Ordem de construção recomendada

| Ordem | Componente | Marco | Status (2026-07-10) |
|---|---|---|---|
| **1** | C0 Docs | Marco 1 | ✅ Feito |
| **2** | C1 Limpeza + schema | Marco 1 | ✅ Shipped (`ingest`) |
| **3** | C2 Features Mix A/B/C | Marco 1 | ✅ Integrado I3 |
| **4** | C3 + C4 + C5 Cascata | Marco 2 | ✅ Shipped (`simulate`) |
| **5** | C6 Matrizes A/B/C | Marco 2 | ✅ Shipped MVP (`accept`) |
| **6** | C8 UI mínima (upload + TSA) | Marco 2 (31/08) | ✅ Shipped (`serve` + `web/`) |
| **7** | C7 UI + relatório detratores | Marco 2–3 | 🔶 Parcial (L3+L4+panel) |
| **8** | Gate A∧B∧C verde | Marco 2–3 | ⚠️ MAE > 56; iterar L2/L3 |
| **9** | C6 Matriz B completa (TC-01…08) | Marco 3 | ⚠️ Débito Marco 2 |
| **10** | C3b Casca / NN | Marco 3+ | Fora MVP |
| **11** | C9 Relatório final | Marco 4 | Pendente |

---

## 6. Dependências externas (fora do código)

| Dependência | Dono | Impacto se atrasar |
|---|---|---|
| Tabelas analíticas limpas / interpoladas (TI) | TI Veracel/Keyrus | Qualidade L2; PRD prevê ganho de ~22 dias se entregue |
| Validação de faixas com processo (se reabrir 0,88) | Stakeholder / Processo | Baixo — valores já otimizados pelos dados |
| Template oficial de planilha de cenário | CD + negócio | Publicado em `template_cenario_v0` (Camada 1); UI ainda consome |
| Definição do holdout temporal | CD + stakeholder | **Fechado:** treino até 2025-04; holdout 2025-05→10 (`config/simulation.yaml`) |

---

## 7. Pontos ainda pendentes

### Bloqueantes para homologação produtiva (não para demo)

1. **MAE ≤ 56** — holdout ~94–97; roadmap em `docs/analysis/DIAGNOSTICO_MAE_ELO3.md`.
2. **Matriz B completa** — MVP cobre TC-03/05 + TM; expandir TC-01…02, TC-04, TC-06…08.
3. **C8 homologação produtiva** — bind `demo=false` na UI, paridade validação, auth serving.

### Qualidade de dados (impacta modelagem, não o backbone)

4. **Issues L2 documentados** — `docs/analysis/RELATORIO_DADOS_ENGENHARIA_VARIAVEIS.md` (proxy DB, cobertura Extrativo, etc.).
5. **Entrega TI da base interpolada** — melhora cobertura; ingest já opera com Excel consolidado.

### Débitos técnicos Marco 2

6. **AT-011** — benchmark p95 infer < 5s (L3).
7. **AT-011/012/017 E2E dedicados** — ingest (parcialmente cobertos).
8. **MLflow / lock distribuído** — ADR-003; filesystem no MVP.

### Decisões de escopo fechadas (não pendência)

- **Elo 1b (% Casca):** NO-GO MVP (D-B).
- **Redes Neurais:** opcional pós-gate.
- **Caminho da Volta, cloud, RCA, retreino UI:** fora do MVP.

### Riscos técnicos a monitorar

9. **Erro composto da cascata** — maior ameaça ao MAE 56; MAE por elo registrado desde L3.
10. **Cobertura de Extrativo_AT** — esparsa antes de 2024; OOF stack mitiga parcialmente.
11. **Sítios D/MG** — poucos casos; testes físicos majoritariamente sintéticos/YAML.

---

## 8. Pacotes de trabalho (status backlog)

| Pacote | Componentes | Resultado | Status |
|---|---|---|---|
| **P1 — Dados** | C1 + C2 | Dataset + features auditáveis | ✅ Shipped |
| **P2 — Cascata** | C3 + C4 + C5 | Modelos encadeados + candidatos L3 | ✅ Shipped |
| **P3 — Aceite** | C6 + C7 | Matrizes A/B/C + explicabilidade | ✅ MVP (`accept`); gate verde pendente |
| **P4 — Produto** | C8 + template | Simulador homologável | ✅ MVP demo; homologação prod pendente |
| **P5 — Fechamento** | C9 (+ C3b/NN se go) | Relatório e encerramento | Pendente |

**Próximo passo natural:** iterar MAE (P2/P3) para `release_ok=true` + homologação produtiva C8 (auth, demo/prod UI).

---

## 9. CLIs e artefatos principais

| CLI | Comando exemplo | Artefato |
|-----|-----------------|----------|
| `ingest` | `ingest batch --source excel.xlsx` | `data/l2/published/{batch_id}/` |
| `simulate` | `simulate train --l2-root data/l2` | `models/candidates/{run_id}/` |
| `simulate` | `simulate infer --cenario-id X --mode A --run-id {id}` | predição Modo A/B |
| `accept` | `accept run --run-id {id}` | `reports/acceptance/{run_id}/acceptance_report.json` |
| `serve` | `serve run --port 8000` | API + SPA (`web/dist`) |
| — | `python scripts/audit_query.py --last 10` | consulta `logs/serving_audit.db` |

Versão do pacote: **0.4.0** (docs); código `pyproject.toml` **0.3.0** até bump formal. Histórico: `docs/CHANGELOG.md`.

---

*Documento de planejamento técnico. Serve como SSOT para decomposição de tarefas do MVP GIFI.*

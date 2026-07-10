# Reanálise de cobertura — Ingest Engine × KB × Agentes

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 1.0  
**Escopo:** somente `docs/sketch/ingest-engine.md` (Camada 2 / I1–I5)  
**Método:** cruzamento seção a seção + AgentSpec MCP (`route_agent`, `kb_search`, `kb_read`) + Context7 (Pydantic)

---

## 1. Veredito

| Pergunta | Resposta |
|----------|----------|
| Precisa criar **novas KBs de domínio** para o Ingest? | **Não** |
| Precisa criar **novos agentes** só para o Ingest? | **Não** |
| Precisa **estender** KBs já existentes? | **Sim (opcional, P1)** — 2–3 specs/patterns dentro de `gifi-ingest` |
| Backend AgentSpec global cobre o resto? | **Sim** — reutilizar, não replicar |

Os gaps restantes são **extensões atômicas** da KB `gifi-ingest` (lista de colunas, evidência de remediação, logging de I5), não novos especialistas.

---

## 2. Cobertura por componente do plano

| § / Componente | Cobertura local | Cobertura AgentSpec (MCP) | Lacuna? |
|----------------|-----------------|---------------------------|---------|
| §1.1 Dual-path | `gifi-ingest/patterns/dual-path-execution` | — | Fechada |
| I1 Conectores | `spreadsheet-connectors/*` | `python`, `pydantic` | Fechada |
| I2 Validação | `gifi-domain` + sinais ingest | `data-quality` (schema-validation, contracts), `data-contracts-engineer` (score 17) | Fechada |
| I3 Transformação | `gifi-domain` mix/ponderação/0,985 | `python` | Fechada |
| I4 Publicação | `artifact-contract.yaml` + `feature-columns.yaml` (2026-07-09) | `medallion` gates; training-data-pipelines | **Fechada** (lista de colunas publicada) |
| I5 Logs/sinais | catálogo + remediação | `data-quality/observability`; `medallion/data-quality-gates` (quarentena); AWS Powertools logging (se cloud) | **Parcial** — schema de **evidência** e padrão de log estruturado MVP |
| §3 Remediação | `remediation-cycle.md` | quarentena medallion | Fechada (evidência: P1) |
| §3.1 Warnings | `warning-matrix.yaml` | — | Fechada |
| §4 Interface Backbone | concepts + specs | ODCS via `data-contracts-engineer` | Fechada para execução |
| §7 TCs P01/08/A02 | mapeados no domínio + casos de teste | `test-generator`, `data-quality-analyst` | Fechada (sem agente novo) |
| Orquestração batch | não bloqueia MVP | `airflow-specialist` (score 15), `pipeline-architect` | Fechada — só se/quando houver DAG |
| UI upload | fora do crítico ingest | `frontend-react` (já no repo) + path online ingest | Fora do escopo desta reanálise |

---

## 3. KBs — adquirir vs reutilizar vs estender

### 3.1 Não adquirir (domínio novo)

Descartado criar KBs novas do tipo `gifi-observability`, `gifi-parquet`, `gifi-testing` etc. Motivos MCP:

| Tema | Onde já existe (AgentSpec) |
|------|----------------------------|
| Quarentena / quality gates | `medallion/patterns/data-quality-gates.md` |
| Observabilidade de dados | `data-quality/concepts/observability.md` |
| Validação schema/Pydantic | `data-quality/patterns/schema-validation.md` + Context7 `/pydantic/pydantic` |
| Contratos ODCS | `data-quality/concepts/data-contracts.md` → agente `data-contracts-engineer` |
| Versionamento dataset/manifest | `ai-data-engineering/patterns/training-data-pipelines.md` |
| Orquestração | `airflow/*` |

### 3.2 Já adquiridas (manter)

- `gifi-domain`
- `gifi-ingest`
- `spreadsheet-connectors`

### 3.3 Extensões recomendadas (P1 — mesmo domínio `gifi-ingest`)

| Artefato | Motivo (plano §) | Status |
|----------|------------------|--------|
| `specs/feature-columns.yaml` | §4.2 lista fixa | **Feito** (0.1.3) |
| `specs/remediation-evidence.yaml` ou pattern | §3 passo 7 / I5 | Pendente P1 |
| `patterns/structured-logging.md` (opcional) | I5 logging | Pendente P1 |

Sem isso o build ainda parte; o risco é drift de schema feature e auditoria incompleta na remediação.

---

## 4. Agentes — criar vs reutilizar

### 4.1 Não criar novos agentes de Ingest

`gifi-domain-specialist` + `gifi-ingest-engineer` cobrem o motor normativo e o I1–I5. Router MCP não descobriu lacuna que exija terceiro especialista GIFI para o plano de ingestão.

### 4.2 Reutilizar AgentSpec (escalation)

| Quando | Agente | Score / nota MCP |
|--------|--------|------------------|
| ODCS / semver artefato | `data-contracts-engineer` | 17 |
| GE/Soda / observability | `data-quality-analyst` | presente |
| pytest TC-P01/08/A02 | `test-generator` (+ ingest-engineer) | preferir sobre GenAI falso-positivo |
| Código Python | `python-developer` | — |
| Layout Bronze/Silver | `medallion-architect` | gates/quarentena |
| DAG batch (pós-MVP ops) | `airflow-specialist` / `pipeline-architect` | 15 / 9 |
| DVC / training dataset versioning | padrões via `ai-data-engineer` KB | training-data-pipelines |

**Ignorar no Ingest:** `llm-specialist`, GenAI/Vertex, `qdrant`, `fabric-logging` (salvo stack Fabric), streaming Kafka — falso positivo ou fora do MVP determinístico.

### 4.3 Agentes já no `_index` fora do Ingest

`gifi-simulation-engineer`, `gifi-acceptance-engineer`, `react-frontend-architect` + KBs `ml-tabular` / `frontend-react` atendem **Camadas 3–5**, não fecham buraco do `ingest-engine.md`. Não entram nesta decisão de aquisição do Ingest.

---

## 5. Mapa de confiança

| Camada de conhecimento | Confidence | Fonte |
|------------------------|------------|-------|
| Plano ingest-engine | 0.95 | doc oficial |
| KBs locais I1–I5 | 0.90–0.95 | docs/kb |
| AgentSpec data-quality / medallion | 0.90–0.95 | MCP Validated 2026-03-26 |
| Pydantic na fronteira I2 | 0.90 | Context7 + schema-validation KB |
| Extensão feature-columns | n/a até escrever | gap documentado |

---

## 6. Próximos passos sugeridos (ordem)

1. **P1** — escrever `gifi-ingest/specs/feature-columns.yaml` (com `gifi-domain-specialist` + `data-contracts-engineer`)
2. **P1** — schema de evidência de remediação em `gifi-ingest`
3. **Build** — SDD Define/Design do Ingest com `gifi-ingest-engineer`
4. **Ops (não bloqueia)** — só então avaliar DAG Airflow

---

*Reanálise somente do Ingest. Visual: `graphics/reanalise_ingest_cobertura.html`.*

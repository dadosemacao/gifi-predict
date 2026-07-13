# CHANGELOG — docs/kb

**Autor:** Emerson Antônio  
**Data:** 2026-07-13

## [0.2.5] — 2026-07-13

### Changed

- `gifi-domain/concepts/operational-bands.md` — adicionada a cobertura das nove variáveis obrigatórias das APIs Forecast e Predict-TSA, distinguindo intervalos empíricos de zonas normativas.
- Registradas explicitamente as quatro variáveis sem faixa normativa (`secura_pct`, `extrativo_total`, `extrativo_sgf` e `idade`), sem alterar `specs/operational-ranges.yaml`.

## [0.2.4] — 2026-07-10

### Added (Sprint P0+P1 — alinhamento Ingest)

- `gifi-domain/specs/template_cenario_v0.yaml` — contrato publicado Camada 1 (bootstrap I1 cenário).
- `gifi-ingest/specs/remediation-evidence.yaml` — esquema evidência ciclo remediação §3.
- `gifi-ingest/patterns/structured-logging.md` — contrato mínimo I5 (JSON por evento).

### Changed

- `ingest-engine.md` v1.2 — P0: I1 template L1, I3 D-C fechada, §4.1 markdown, Elo 1b removido.
- `analytical-backbone.md` v1.1 — template na Camada 1; Camada 5 = instância upload.
- `domain-rules.yaml` — `scenario_template.spec` aponta para template v0.
- `_index.yaml` v0.2.4 — novos specs/patterns indexados.

## [0.2.3] — 2026-07-09

### Added (extensões P1 — sem novos domínios/agentes)

- `ml-tabular/patterns/matriz-c-detractors.md` — top-3 ΔTSA (SHAP / coef / permutation); Context7 shap + sklearn.
- `ml-tabular/patterns/inference-serving.md` — FastAPI upload → curves + detractors; Context7 FastAPI.
- `frontend-react/patterns/production-curves-chart.md` — Recharts multi-series presentational; Context7 Recharts.
- `gifi-domain/patterns/adherence-report.md` — relatório de aderência / desvios assistidos (Marco 4).
- Indexes + quick-references + `_index.yaml` v0.2.3 atualizados; espelho AgentSpec/MCP.

### Notes

- Line limits: patterns &lt; 200; QRs revisados.
- Sem novos agentes; reuso simulation / acceptance / react-frontend + python-developer.

## [0.2.2] — 2026-07-09

### Added

- `generate-agent-router.py` no AgentSpec local (layout `agents/`, categoria `gifi`).
- Agent-router regenerado: 63 agentes, 9 categorias, hash `4af6351345b8`.
- Cinco agentes GIFI sincronizados em `agentspec/agents/gifi/` e espelho Cursor.

### Notes

- Comando: `cd ~/.cursor/plugins/local/agentspec && python3 scripts/generate-agent-router.py --check`

## [0.2.1] — 2026-07-09

### Added

- Skills Cursor: `gifi-simulation-engineer`, `gifi-acceptance-engineer`, `react-frontend-architect`.
- Espelho das KBs P0 no path MCP (`dist/mcp/resources/kb`) e caches AgentSpec.
- Skills registrados em `_index.yaml` (`agents.*.skill`).

### Notes

- Roteamento operacional no projeto: `.cursor/rules/gifi-agents.mdc`.

## [0.2.0] — 2026-07-09

### Added

- Expansão P0 `gifi-domain`: platform-layers, operational-bands, acceptance-matrices; patterns mix-abc, turno-dia, champion-policy, scenario-column-contract.
- Domínio `ml-tabular` (cascata Elo1→2→3, EN/RF, holdout, métricas, física + 4 patterns).
- Domínio `frontend-react` (stack Vite/React, 4 concepts + 8 design patterns).
- Agentes draft: `gifi-simulation-engineer`, `gifi-acceptance-engineer`, `react-frontend-architect`.
- Registro: `docs/sketch/AGENTES_E_KB_BACKBONE.md`.
- Espelho no AgentSpec local: `kb/{gifi-domain,ml-tabular,frontend-react}` + `agents/gifi/`; `_index.yaml` v2.3.

### Notes

- Confidence: gifi-domain/ml-tabular 0.95; frontend-react 0.90 (MCP React/Query/Zod).
- Router script `generate-agent-router.py` ausente no install — regeneração manual pendente.

## [0.1.3] — 2026-07-09

### Added

- `gifi-ingest/specs/feature-columns.yaml` — lista fixa (processo, Lab/SGF, abastecimento/mix)
- `gifi-ingest/concepts/feature-column-contract.md`
- Mapa negócio→canônico: VMI flags, `pct_AB`, `pct_DMG` + Camada B/C PRD

## [0.1.2] — 2026-07-09

### Added

- `REANALISE_INGEST_COBERTURA.md` + `graphics/reanalise_ingest_cobertura.html`
- Veredito MCP: não adquirir novas KBs/agentes para o Ingest; extensões P1 em `gifi-ingest`

## [0.1.1] — 2026-07-09

### Added

- Agentes projeto: `.cursor/agents/gifi-domain-specialist.md`, `.cursor/agents/gifi-ingest-engineer.md`
- Skills Cursor: `.cursor/skills/gifi-domain-specialist/`, `.cursor/skills/gifi-ingest-engineer/`
- Regra de roteamento: `.cursor/rules/gifi-agents.mdc`
- Registro `agents:` em `_index.yaml`

## [0.1.0] — 2026-07-09

### Added

- Domínio `gifi-domain` (v0.1): conceitos, padrões, specs YAML de regras e faixas.
- Domínio `gifi-ingest` (v0.1): mapa I1–I5, catálogo de sinais, contratos, matriz de warnings.
- Domínio `spreadsheet-connectors` (v0.1): modos de fonte, identidade de lote, Excel/TI/cenário.
- Manifesto `_index.yaml` compatível com estrutura AgentSpec KB.

### Notes

- Fontes: PRD v1.1, ingest-engine.md, faixas operacionais, DECISOES_GIFI.
- Confidence: 0.95 (domain/ingest) / 0.85 (spreadsheet — sem MCP Excel dedicado).

### Validation score (estrutura KB Architect)

| Check | Score |
|-------|------:|
| Structure (dirs) | 25/25 |
| Atomicity (line limits) | 20/20 |
| Navigation (index + QR) | 15/15 |
| Manifest (_index.yaml) | 15/15 |
| Validation dates | 15/15 |
| Cross-refs | 10/10 |
| **Total** | **100/100** |

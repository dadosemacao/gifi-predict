# Bases de Conhecimento do Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 0.2

KBs locais no formato AgentSpec (index / quick-reference / concepts / patterns / specs).

| Domínio | Path | Uso |
|---------|------|-----|
| `gifi-domain` | [gifi-domain/](gifi-domain/) | Camada 1 — SSOT (camadas, faixas, A/B/C) |
| `ml-tabular` | [ml-tabular/](ml-tabular/) | Camada 3 — cascata tabular EN/RF |
| `frontend-react` | [frontend-react/](frontend-react/) | Camada 5 — UI React+Vite |
| `gifi-ingest` | [gifi-ingest/](gifi-ingest/) | Ingest Engine I1–I5 |
| `spreadsheet-connectors` | [spreadsheet-connectors/](spreadsheet-connectors/) | Conectores Excel/TI/upload |

Manifesto: [`_index.yaml`](_index.yaml) · Histórico: [`CHANGELOG.md`](CHANGELOG.md)  
Registro AgentSpec: [`docs/sketch/AGENTES_E_KB_BACKBONE.md`](../sketch/AGENTES_E_KB_BACKBONE.md)

## Agentes do projeto

| Agente | Definição | Camada |
|--------|-----------|--------|
| `gifi-domain-specialist` | [`.cursor/agents/gifi-domain-specialist.md`](../../.cursor/agents/gifi-domain-specialist.md) | 1 |
| `gifi-ingest-engineer` | [`.cursor/agents/gifi-ingest-engineer.md`](../../.cursor/agents/gifi-ingest-engineer.md) | 2 |
| `gifi-simulation-engineer` | [`.cursor/agents/gifi-simulation-engineer.md`](../../.cursor/agents/gifi-simulation-engineer.md) | 3 |
| `gifi-acceptance-engineer` | [`.cursor/agents/gifi-acceptance-engineer.md`](../../.cursor/agents/gifi-acceptance-engineer.md) | 4 |
| `react-frontend-architect` | [`.cursor/agents/react-frontend-architect.md`](../../.cursor/agents/react-frontend-architect.md) | 5 |

Roteamento: [`.cursor/rules/gifi-agents.mdc`](../../.cursor/rules/gifi-agents.mdc)

Espelho AgentSpec (plugin): `~/.cursor/plugins/local/agentspec/kb/{domain}/` e `agents/gifi/`.

Complementam KBs globais AgentSpec: `data-quality`, `python`, `testing`, etc.

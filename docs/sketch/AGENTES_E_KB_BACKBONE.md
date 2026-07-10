# Agentes e KB — Backbone Analítico GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 1.3  
**Escopo:** Registro de caminhos + reanálise pós-scaffold (necessidade de mais KBs/agentes)

---

## 1. Onde vivem as KBs

| Domínio | Projeto (SSOT de conteúdo GIFI) | AgentSpec plugin (espelho) |
|---------|----------------------------------|----------------------------|
| `gifi-domain` | `/Users/emerson.antonio/Developar/keyrus/veracel/gifi-predict/docs/kb/gifi-domain/` | `~/.cursor/plugins/local/agentspec/kb/gifi-domain/` |
| `ml-tabular` | `.../docs/kb/ml-tabular/` | `~/.cursor/plugins/local/agentspec/kb/ml-tabular/` |
| `frontend-react` | `.../docs/kb/frontend-react/` | `~/.cursor/plugins/local/agentspec/kb/frontend-react/` |
| `gifi-ingest` | `.../docs/kb/gifi-ingest/` | (projeto; espelhar sob demanda) |
| `spreadsheet-connectors` | `.../docs/kb/spreadsheet-connectors/` | (projeto) |

Manifestos:

- Projeto: `docs/kb/_index.yaml` (v0.2.0+)
- AgentSpec: `~/.cursor/plugins/local/agentspec/kb/_index.yaml`
- Cache marketplace MCP: `dist/mcp/resources/kb/`

Ao editar conteúdo normativo GIFI, **preferir o tree do repositório** `docs/kb/` e re-sincronizar para o plugin.

---

## 2. Agentes

| Agente | Camada | `kb_domains` | Paths |
|--------|--------|--------------|-------|
| `gifi-domain-specialist` | 1 | gifi-domain | `.cursor/agents/` + `.cursor/skills/` |
| `gifi-ingest-engineer` | 2 | gifi-ingest, gifi-domain, spreadsheet-connectors | `.cursor/agents/` + `.cursor/skills/` |
| `gifi-simulation-engineer` | 3 | ml-tabular, gifi-domain, python, testing | `.cursor/agents/` + skill + `agentspec/agents/gifi/` |
| `gifi-acceptance-engineer` | 4 | gifi-domain, ml-tabular, testing, data-quality | idem |
| `react-frontend-architect` | 5 | frontend-react, gifi-domain | idem |

AgentSpec category folder:  
`/Users/emerson.antonio/.cursor/plugins/local/agentspec/agents/gifi/`

Roteamento Cursor do projeto: `.cursor/rules/gifi-agents.mdc`

---

## 3. Agent-router AgentSpec (regenerado)

| Item | Valor |
|------|-------|
| Script | `~/.cursor/plugins/local/agentspec/scripts/generate-agent-router.py` |
| Layout | lê `agents/<category>/*.md` (não `.claude/agents`) |
| Saídas | `skills/agent-router/{SKILL.md,routing.json}` + espelho `cursor/skills/agent-router/` |
| Contagem | **63** agentes · **9** categorias · hash `4af6351345b8` |
| Categoria nova | `gifi` — 5 agentes |
| Check | `python3 scripts/generate-agent-router.py --check` → OK |

Artefatos também propagados para `dist/mcp/resources/skills/agent-router/` (fonte do MCP `route_agent`).

### Regenerar após mudar frontmatter

```bash
cd ~/.cursor/plugins/local/agentspec
cp ~/Developar/keyrus/veracel/gifi-predict/.cursor/agents/gifi-*.md agents/gifi/
cp ~/Developar/keyrus/veracel/gifi-predict/.cursor/agents/react-frontend-architect.md agents/gifi/
python3 scripts/generate-agent-router.py
python3 scripts/generate-agent-router.py --check
# propagar para MCP resources (se o MCP estiver ativo, reiniciar o servidor)
cp skills/agent-router/* \
  ~/.cursor/plugins/marketplaces/github.com/emerson-antonio-ops/agentspec/*/dist/mcp/resources/skills/agent-router/
```

---

## 4. Notas

1. Skills Cursor — feitos: domain, ingest, simulation, acceptance, react-frontend.
2. Se `route_agent` MCP ainda devolver ranking legado, reiniciar o servidor MCP AgentSpec (cache em memória).
3. Não versionar o plugin AgentSpec no git do gifi-predict; versionar `docs/kb/`, `.cursor/agents/`, `.cursor/skills/` e `.cursor/rules/`.

---

## 5. Como usar

- Tarefa normativa / faixas / template → `gifi-domain-specialist` + `docs/kb/gifi-domain`
- Ingest / L2 → `gifi-ingest-engineer` + `docs/kb/gifi-ingest`
- Treino cascata / EN-RF / Modo A/B → `gifi-simulation-engineer` + `docs/kb/ml-tabular`
- Gate MAE≤56 / Matriz B/C / campeão → `gifi-acceptance-engineer`
- UI Vite/React → `react-frontend-architect` + `docs/kb/frontend-react`

---

## 6. Reanálise pós-scaffold (2026-07-09)

**Pergunta:** ainda precisamos adquirir mais KBs ou criar mais agentes para a backbone?

**Resposta (MCP `route_agent` + `kb_search` + Context7):** **não** para o MVP.  
Camadas 1–5 já têm dono com score alto (17–29). Gaps restantes são **conteúdo** dentro das KBs existentes.

| Decisão | Detalhe |
|---------|---------|
| Novos agentes | **0** — não criar shap/charts/fastapi/relatório specialists |
| Novos domínios KB | **0** — não criar `shap`, `recharts`, `fastapi`, MLflow |
| Extensões P1 | `ml-tabular` (Matriz C + inference serving); `frontend-react` (curvas Recharts); `gifi-domain` (relatório de aderência) |
| Status P1 | **Feito 0.2.3** — ver `docs/kb/CHANGELOG.md` |
| Reuso | `python-developer`, `test-generator`, `data-quality-analyst`, `data-contracts-engineer`, KB `pydantic`/`python`/`testing` |
| Fora do MVP | Elo 1b, NN, MLflow/Fabric cloud, RCA automática |

Relatório visual: `graphics/agentspec_backbone_reanalise_kb_agentes.html`

MCPs usados na reanálise: AgentSpec (`route_agent`, `kb_search`, `kb_read`), Context7 (sklearn, shap, recharts, FastAPI).

---

*Documento de registro. Não substitui PRD nem analytical-backbone.*

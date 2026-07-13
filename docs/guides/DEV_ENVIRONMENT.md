# Guia de Ambiente de Desenvolvimento — GIFI Predict

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.1

---

## 1. Objetivo

Padronizar ambiente Python/Node, dependências, qualidade de código, serving local e roteamento de agentes especialistas para as Camadas 2–5 do GIFI.

---

## 2. Auditoria (estado em 2026-07-13)

### 2.1 Ambiente virtual

| Item | Estado |
|------|--------|
| `.venv/` no repo | Criado via `scripts/setup_dev.sh` |
| Python em uso | **3.12** (pin em `.python-version`) |
| Instalação | `pip install -e ".[dev]"` dentro do venv |

### 2.2 Dependências

| Abordagem | Status |
|-----------|--------|
| `pyproject.toml` (PEP 621) | Fonte única de verdade |
| `requirements.txt` | Gerado para CI/Docker |
| `requirements-dev.txt` | Gerado com extras `dev` |
| `uv.lock` | Lock file para builds reproduzíveis |
| `web/package.json` | Frontend React/Vite (Node 18+) |

Não mantemos `requirements.txt` manual — sempre regenerar a partir do `pyproject.toml`.

### 2.3 Boas práticas

| Prática | Status |
|---------|--------|
| Layout `src/` | OK — `ingest/`, `simulation/`, `acceptance/`, `serving/` |
| Config externa YAML | OK — `config/*.yaml` |
| Settings tipados (Pydantic) | OK |
| CLI Typer | OK — `ingest`, `simulate`, `accept`, `serve` |
| Testes pytest + marker `@slow` | OK — ~60+ casos Python |
| Vitest (web) | OK — smoke UI |
| SDD rastreável | OK — DEFINE → DESIGN → BUILD → SHIP |
| Linter (ruff) | OK |
| Cobertura (pytest-cov) | OK — inclui `serving` |
| pre-commit | Débito Marco 2 |
| CI pipeline | Débito Marco 2 |

### 2.4 Agentes especialistas

Roteamento canônico (`docs/sketch/AGENTES_E_KB_BACKBONE.md`):

| Camada | Agente | Quando invocar |
|--------|--------|----------------|
| 1 — Domínio | `gifi-domain-specialist` | Faixas, holdout, Modo A/B, template cenário |
| 2 — Ingest | `gifi-ingest-engineer` | I1–I5, L2, sinais, quarentena |
| 3 — Simulação | `gifi-simulation-engineer` | Cascata, EN/RF, champion, Modo A/B, 13 preditores |
| 4 — Aceite | `gifi-acceptance-engineer` | Matrizes A/B/C, gate MAE≤56, release |
| 5 — UI | `react-frontend-architect` | React, curvas, formulários, forecast panels |
| Transversal | `python-developer` | Bootstrap, CLI, refatoração |
| Transversal | `test-generator` | Cobertura AT/TC |
| Transversal | `code-reviewer` | Após cada build significativo |

### 2.5 Evolução de modelos (MLflow)

Ver ADR: [`docs/adr/ADR-003-manifest-vs-mlflow.md`](../adr/ADR-003-manifest-vs-mlflow.md).

**Resumo:** MVP usa manifesto JSON + filesystem (`models/candidates/`, `models/primeira_base/`). MLflow Tracking só no Marco 2, se volume de experimentos justificar.

---

## 3. Setup rápido

```bash
# Python
./scripts/setup_dev.sh
source .venv/bin/activate

# Frontend (primeira vez)
cd web && npm install && cd ..
```

Verificar:

```bash
which python          # .venv/bin/python
python --version      # 3.12.x
pytest tests/ -q -m "not slow"
ingest --help
simulate --help
accept --help
serve --help
```

---

## 4. Comandos do dia a dia

```bash
source .venv/bin/activate

# Testes Python
pytest tests/ -q -m "not slow"
pytest tests/ -m slow -v
pytest tests/ --cov=ingest --cov=simulation --cov=acceptance --cov=serving --cov-report=term-missing

# Testes frontend
cd web && npm test

# Qualidade
ruff check src/ tests/
ruff format --check src/ tests/

# Ingest (Camada 2)
ingest batch "excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx"

# Simulação (Camada 3)
simulate train --l2-root data/l2_excel_validation
simulate evaluate --run-id <run_id>
simulate infer --cenario-id CEN-001 --mode A --run-id <run_id>

# Aceite (Camada 4)
accept run --run-id <run_id>
accept report --run-id <run_id>

# Serving (Camada 5)
serve run --port 8000                    # API + SPA build
./scripts/dev_ui.sh                      # API :8000 + Vite :5173

# Auditoria
python scripts/audit_query.py --last 10
python scripts/audit_query.py --errors
python scripts/audit_query.py --count-24h
```

---

## 5. Desenvolvimento UI

| Modo | Comando | URLs |
|------|---------|------|
| Dev (hot reload) | `./scripts/dev_ui.sh` | API `http://127.0.0.1:8000`, Vite `http://127.0.0.1:5173` |
| Produção local | `cd web && npm run build && cd .. && serve run` | `http://127.0.0.1:8000` (SPA + API) |

Config serving: `config/serving.yaml` — `static_dir: web/dist`, `cors_origins` para Vite dev.

Proxy Vite (`web/vite.config.ts`): `/api` → `:8000`.

---

## 6. Regenerar dependências Python

Quando alterar `pyproject.toml`:

```bash
source .venv/bin/activate
uv lock
uv export --no-dev -o requirements.txt
uv export --extra dev -o requirements-dev.txt
pip install -e ".[dev]"
```

---

## 7. Versão Python suportada

| Versão | Suporte |
|--------|---------|
| 3.12 | **Recomendada** (pin `.python-version`) |
| 3.11 | Suportada (`requires-python >=3.11`) |
| 3.14 | Não recomendada (sklearn pode variar) |

---

## 8. Estrutura de pacotes

```text
src/
  ingest/       Camada 2 — Ingest Engine
  simulation/   Camada 3 — Motor de Simulação
  acceptance/   Camada 4 — Gate de Aceite
  serving/      Camada 5 — FastAPI + observability
web/
  src/          Camada 5 — React SPA
config/
  ingest.yaml
  simulation.yaml
  acceptance.yaml
  serving.yaml
tests/
  ingest/
  simulation/
  acceptance/
  serving/
models/         Candidatos L3 + campeão + primeira_base (gitignored)
data/l2/        Artefatos L2 (gitignored)
logs/           Audit DB + logs de treino (gitignored)
docs/api/       Dicionários REST
```

---

## 9. Checklist onboarding (novo dev)

- [ ] Clonar repo
- [ ] `./scripts/setup_dev.sh`
- [ ] `cd web && npm install`
- [ ] `pytest tests/ -q -m "not slow"` verde
- [ ] Ler `docs/PRD_GIFI_v1.1.md`
- [ ] Ler `docs/sketch/AGENTES_E_KB_BACKBONE.md`
- [ ] Ler `docs/api/README.md`
- [ ] Rodar `./scripts/dev_ui.sh` e validar três abas da UI
- [ ] Rodar ingest batch no Excel de exemplo (opcional)

---

## 10. Débito Marco 2–3

- Pipeline CI (GitHub Actions / Azure DevOps)
- pre-commit hooks (ruff + pytest smoke)
- Segurança serving — ver [`SECURITY_SERVING_DEBITOS.md`](SECURITY_SERVING_DEBITOS.md) (auth, rate limit, path traversal, upload limits, joblib)
- Playwright E2E
- Pin explícito de cobertura mínima no CI

**Fechado em 2026-07-13:** paridade Zod ↔ Pydantic e toggle demo/prod na UI —
ver [`../api/GAPS_UI_E_VALIDACAO.md`](../api/GAPS_UI_E_VALIDACAO.md).

---

*Documento vivo. Atualizar ao mudar toolchain, serving ou política de agentes.*

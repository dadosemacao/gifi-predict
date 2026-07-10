# Guia de Ambiente de Desenvolvimento — GIFI Predict

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Versão:** 1.0

---

## 1. Objetivo

Padronizar ambiente Python, dependências, qualidade de código e roteamento de agentes especialistas para as Camadas 2–5 do GIFI.

---

## 2. Auditoria (estado em 2026-07-10)

### 2.1 Ambiente virtual

| Item | Estado anterior | Estado alvo |
|------|-----------------|-------------|
| `.venv/` no repo | Ausente | Criado via `scripts/setup_dev.sh` |
| Python em uso | 3.14 (sistema) | **3.12** (pin em `.python-version`) |
| Instalação | `pip install -e .` global | Editable dentro do venv |

**Risco mitigado:** dependências isoladas, compatibilidade estável com `scikit-learn`.

### 2.2 Dependências

| Abordagem | Status |
|-----------|--------|
| `pyproject.toml` (PEP 621) | Fonte única de verdade |
| `requirements.txt` | Gerado para CI/Docker legado |
| `requirements-dev.txt` | Gerado com extras `dev` |
| `uv.lock` | Lock file para builds reproduzíveis |

Não mantemos `requirements.txt` manual — sempre regenerar a partir do `pyproject.toml`.

### 2.3 Boas práticas Python

| Prática | Status |
|---------|--------|
| Layout `src/` | OK — `src/ingest/`, `src/simulation/` |
| Config externa YAML | OK — `config/ingest.yaml`, `config/simulation.yaml` |
| Settings tipados (Pydantic) | OK |
| CLI Typer | OK — `ingest`, `simulate` |
| Testes pytest + marker `@slow` | OK — 26 testes |
| SDD rastreável | OK — DEFINE → DESIGN → BUILD → SHIP |
| Linter (ruff) | Adicionado |
| Cobertura (pytest-cov) | Adicionado |
| pre-commit | Débito Marco 2 |
| CI pipeline | Débito Marco 2 |

### 2.4 Agentes especialistas

Roteamento canônico (`docs/sketch/AGENTES_E_KB_BACKBONE.md`):

| Camada | Agente | Quando invocar |
|--------|--------|----------------|
| 1 — Domínio | `gifi-domain-specialist` | Faixas, holdout, Modo A/B, `elo_specs`, template cenário |
| 2 — Ingest | `gifi-ingest-engineer` | I1–I5, L2, sinais, quarentena |
| 3 — Simulação | `gifi-simulation-engineer` | Cascata, EN/RF, champion, Modo A/B |
| 4 — Aceite | `gifi-acceptance-engineer` | Matrizes A/B/C, gate MAE≤56, release |
| 5 — UI | `react-frontend-architect` | React, curvas, formulários cenário |
| Transversal | `python-developer` | Bootstrap, CLI, refatoração |
| Transversal | `test-generator` | Cobertura AT/TC |
| Transversal | `code-reviewer` | Após cada `/build` significativo |

**Regra SDD:** o `/build` pode executar monoliticamente, mas cada fase deve **registrar** qual agente validou decisões normativas (domínio, aceite).

### 2.5 Evolução de modelos (MLflow)

Ver ADR dedicado: [`docs/adr/ADR-003-manifest-vs-mlflow.md`](../adr/ADR-003-manifest-vs-mlflow.md).

**Resumo:** MVP usa manifesto JSON + filesystem (`models/candidates/`). MLflow Tracking só no Marco 2, se volume de experimentos justificar.

---

## 3. Setup rápido

```bash
# Opção A — script automatizado (recomendado)
./scripts/setup_dev.sh

# Opção B — manual
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

Verificar:

```bash
which python    # deve apontar para .venv/bin/python
python --version  # Python 3.12.x
pytest tests/ -q
ingest --help
simulate --help
```

---

## 4. Comandos do dia a dia

```bash
source .venv/bin/activate

# Testes
pytest tests/ -q                    # rápido (sem @slow)
pytest tests/ -m slow -v            # smoke Excel L2
pytest tests/ --cov=ingest --cov=simulation --cov-report=term-missing

# Qualidade
ruff check src/ tests/
ruff format --check src/ tests/

# Ingest (Camada 2)
ingest batch "excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx"

# Simulação (Camada 3)
simulate train --l2-root data/l2_excel_validation
simulate evaluate
simulate infer --cenario-id CEN-001 --mode A
```

---

## 5. Regenerar dependências

Quando alterar `pyproject.toml`:

```bash
source .venv/bin/activate
uv lock
uv export --no-dev -o requirements.txt
uv export --extra dev -o requirements-dev.txt
pip install -e ".[dev]"
```

---

## 6. Versão Python suportada

| Versão | Suporte |
|--------|---------|
| 3.12 | **Recomendada** (pin `.python-version`) |
| 3.11 | Suportada (`requires-python >=3.11`) |
| 3.14 | Não recomendada (dev local apenas; sklearn pode variar) |

---

## 7. Estrutura de pacotes

```text
src/
  ingest/       Camada 2 — Ingest Engine
  simulation/   Camada 3 — Motor de Simulação
config/
  ingest.yaml
  simulation.yaml
tests/
  ingest/
  simulation/
models/         Candidatos L3 (gitignored)
data/l2/        Artefatos L2 (gitignored)
```

---

## 8. Checklist onboarding (novo dev)

- [ ] Clonar repo
- [ ] `./scripts/setup_dev.sh`
- [ ] `pytest tests/ -q` verde
- [ ] Ler `docs/PRD_GIFI_v1.1.md`
- [ ] Ler `docs/sketch/AGENTES_E_KB_BACKBONE.md`
- [ ] Rodar ingest batch no Excel de exemplo (opcional)
- [ ] Rodar `simulate train` com `data/l2_excel_validation` (opcional)

---

## 9. Débito Marco 2

- Pipeline CI (GitHub Actions / Azure DevOps)
- pre-commit hooks (ruff + pytest smoke)
- Pin explícito de cobertura mínima no CI
- Invocação formal de subagentes por fase SDD

---

*Documento vivo. Atualizar ao mudar toolchain ou política de agentes.*

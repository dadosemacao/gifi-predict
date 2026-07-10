# GIFI — Simulador Preditivo de Produção de Celulose (TSA/dia)

**Autor:** Emerson Antônio (Cientista de Dados)  
**Stakeholder:** Thiago Taglialegna Salles  
**Time:** Keyrus | Veracel — Squad Sustentação  
**Status:** Camadas 2–4 implementadas (v0.3.0) — próximo: Camada 5 (UI demo)

---

## 1. Problema

O planejamento florestal e industrial da Veracel não consegue prever a produção real de celulose (**TSA/dia**) em cenários de longo prazo (2025/2026). Os modelos anteriores dependiam de variáveis de janela móvel (**lags**), o que impede simular talhões ainda não cortados.

## 2. Solução

Um **simulador preditivo em cascata** (Caminho da Ida) que estima TSA/dia apenas com variáveis de planejamento de abastecimento, sem lags:

```
Planejamento (mix, sítio, idade, TPC, volume, DB_SGF, Kappa)
        │
   Elo 1 → Extrativo Álcool-Toluol
   Elo 2 → Carga Alcalina
   Elo 3 → TSA/dia
        │
   Interface web: curva de TSA + top-3 detratores
```

Elo 1b (% Casca) é **NO-GO no MVP**; casca entra como feature do Elo 3 apenas quando medida.

## 3. Critérios de aceite (Matrizes A/B/C)

| Matriz | Critério |
|--------|----------|
| **A — Estatística** | `MAE ≤ 56 TSA/dia` no holdout temporal **2025-05 a 2025-10** (treino até 2025-04) |
| **B — Física** | Monotonicidade: DB↓, VMI↓, Extrativos↑, TPC<45, Carga↑ → TSA↓ |
| **C — Explicabilidade** | Top-3 detratores com contribuição em ΔTSA por cenário |

Release do MVP exige **A ∧ B ∧ C** (não intercambiáveis). Interface homologável até **31/08/2026**.

## 4. Parâmetros oficiais (evidência da base 2018–2025)

| Variável | Unidade | Ótima | Crítica |
|----------|---------|-------|---------|
| DB_LAB | kg/m³ | 470–510 | <450 ou >520 |
| Extrativo AT | % | 1,5–2,1 | >2,45 |
| TPC | dias | 60–90 | <45 (madeira verde) |
| Carga Alcalina | % Na₂O | 18,5–20,5 | >21,0 |
| Kappa | — | 16–18 | <15 ou >18,5 |

Imputação de densidade: `DB_LAB = 0,985 × DB_SGF` (fator legado 0,88 obsoleto).

## 5. Arquitetura (5 camadas)

```text
Camada 1 — Domínio (regras, faixas, Modo A/B)
Camada 2 — Ingest Engine          ← implementado (v0.1.0)
Camada 3 — Motor de Simulação     ← implementado (v0.2.x)
Camada 4 — Confiança e Aceite     ← implementado (v0.3.0)
Camada 5 — Superfície de Uso (UI React)  ← próximo
```

Mapa de componentes: [`docs/sketch/MAPA_COMPONENTES_GIFI.md`](docs/sketch/MAPA_COMPONENTES_GIFI.md)

Diagrama geral: `graphics/mapa_componentes_gifi.png`  
Diagramas do Ingest: [`docs/diagrams/INGEST_ENGINE.md`](docs/diagrams/INGEST_ENGINE.md)

---

## 6. Setup do ambiente

**Python recomendado:** 3.12 (ver `.python-version`)

```bash
./scripts/setup_dev.sh
source .venv/bin/activate
```

Guia completo: [`docs/guides/DEV_ENVIRONMENT.md`](docs/guides/DEV_ENVIRONMENT.md)

Dependências:

| Arquivo | Uso |
|---------|-----|
| `pyproject.toml` | Fonte única de verdade |
| `uv.lock` | Lock file reproduzível |
| `requirements.txt` | CI/Docker (gerado via `uv export`) |
| `requirements-dev.txt` | Dev + testes + ruff |

---

## 7. Ingest Engine (Camada 2)

Transforma Excel QM×Processo e uploads de cenário em artefatos L2 versionados (Parquet + manifesto JSON).

```bash
ingest batch "excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx"
ingest scenario-validate uploads/cenario.csv --cenario-id CEN-001
ingest scenario-publish uploads/cenario.csv --cenario-id CEN-001
ingest reprocess
```

**Validação Excel real (2026-07-10):** 7.573 turnos → 7.064 train + 500 holdout.

---

## 8. Motor de Simulação (Camada 3)

Treina cascata Elo 1→2→3 (Baseline / ElasticNet / RandomForest), avalia holdout e empacota candidatos em `models/`.

```bash
simulate train --l2-root data/l2_excel_validation
simulate evaluate --run-id <run_id>
simulate infer --cenario-id CEN-001 --mode A --run-id <run_id>
```

| Artefato L3 | Uso |
|-------------|-----|
| `models/candidates/{run_id}/` | Joblibs + manifesto + métricas + explainability |
| `current_candidate.json` | Pointer last-good (só se `release_ok=true`) |

Evolução de modelos: manifesto JSON local (sem MLflow no MVP). Ver [`docs/adr/ADR-003-manifest-vs-mlflow.md`](docs/adr/ADR-003-manifest-vs-mlflow.md).

---

## 9. Gate de Aceite (Camada 4)

Executa Matrizes A∧B∧C sobre candidatos L3 e gera relatório auditável. Com MAE atual ~94–97, o gate retorna `demo_mode=true` (esperado até iterar modelagem).

```bash
accept run --run-id <run_id> --l2-root data/l2_excel_validation
accept report --run-id <run_id>
```

| Artefato L4 | Uso |
|-------------|-----|
| `reports/acceptance/{run_id}/acceptance_report.json` | Flags `matriz_a/b/c`, `release_ok`, `demo_mode` |
| `models/champion/{run_id}/` | Campeão produtivo (somente se `release_ok=true`) |

---

## 10. Testes e qualidade

```bash
pytest tests/ -q -m "not slow"     # unitários (rápido)
pytest tests/ -m slow -v           # smoke Excel L2
pytest tests/ --cov=ingest --cov=simulation --cov=acceptance --cov-report=term-missing
ruff check src/ tests/
```

---

## 11. Estrutura do repositório

```text
src/ingest/           Camada 2 — Ingest Engine
src/simulation/       Camada 3 — Motor de Simulação
src/acceptance/       Camada 4 — Gate de Aceite
config/               ingest.yaml, simulation.yaml, acceptance.yaml
tests/ingest/         Testes L2
tests/simulation/     Testes L3
tests/acceptance/     Testes L4
scripts/setup_dev.sh  Bootstrap do venv
data/l2/              Artefatos L2 (gitignored)
models/               Candidatos L3 + campeão (gitignored)
reports/acceptance/   Relatórios de gate (gitignored)
docs/guides/          Guias de desenvolvimento
docs/adr/             Architecture Decision Records
docs/kb/              Knowledge base normativa
```

---

## 12. Documentação

| Documento | Conteúdo |
|-----------|----------|
| `docs/guides/DEV_ENVIRONMENT.md` | Ambiente, agentes, toolchain |
| `docs/sketch/MAPA_COMPONENTES_GIFI.md` | Mapa C0–C9 e status das camadas |
| `docs/adr/ADR-003-manifest-vs-mlflow.md` | Decisão MLOps / MLflow |
| `docs/PRD_GIFI_v1.1.md` | Requisitos do produto |
| `docs/sketch/AGENTES_E_KB_BACKBONE.md` | Roteamento de agentes |
| `docs/diagrams/INGEST_ENGINE.md` | Diagrama L2 |
| `docs/analysis/DIAGNOSTICO_MAE_ELO3.md` | Gap MAE vs gate 56 |
| `docs/CHANGELOG.md` | Histórico de versões |

---

## 13. Agentes especialistas (SDD)

| Camada | Agente |
|--------|--------|
| Domínio | `gifi-domain-specialist` |
| Ingest | `gifi-ingest-engineer` |
| Simulação | `gifi-simulation-engineer` |
| Aceite | `gifi-acceptance-engineer` |
| UI | `react-frontend-architect` |

---

## 14. Pendências (Marco 2)

- Camada 5 — UI React (modo demo com `demo_mode` do acceptance report)
- Gate A∧B∧C verde — iterar L2/L3 (MAE ~94–97 vs gate 56)
- Matriz B completa — expandir TC-01…08 além do MVP (TC-03/05 + TM)
- CI pipeline + pre-commit

---

*Projeto conduzido sob rastreabilidade documental. Alterações a decisões confirmadas exigem solicitação formal de mudança.*

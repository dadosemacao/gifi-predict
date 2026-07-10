# GIFI — Simulador Preditivo de Produção de Celulose (TSA/dia)

**Autor:** Emerson Antônio (Cientista de Dados)  
**Stakeholder:** Thiago Taglialegna Salles  
**Time:** Keyrus | Veracel — Squad Sustentação  
**Status:** Camada 2 (Ingest Engine) implementada — Camada 3 em planejamento

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
Camada 2 — Ingest Engine     ← implementado (v0.1.0)
Camada 3 — Motor de Simulação (cascata Elo 1→2→3)
Camada 4 — Confiança e Aceite (Matrizes A/B/C)
Camada 5 — Superfície de Uso (UI React)
```

Diagrama geral: `graphics/mapa_componentes_gifi.png`  
Diagramas do Ingest: [`docs/diagrams/INGEST_ENGINE.md`](docs/diagrams/INGEST_ENGINE.md)

---

## 6. Ingest Engine (Camada 2) — uso rápido

Transforma Excel QM×Processo e uploads de cenário em artefatos L2 versionados (Parquet + manifesto JSON).

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Comandos CLI

```bash
# Batch histórico (Excel ou CSV)
ingest batch "excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx"

# Cenário online (Modo B)
ingest scenario-validate uploads/cenario.csv --cenario-id CEN-001
ingest scenario-publish uploads/cenario.csv --cenario-id CEN-001

# Reprocesso após ACCEPT_DATA_REJECT
ingest reprocess
```

### Testes

```bash
pytest tests/ingest -q                  # unitários (rápido)
pytest tests/ingest -m slow -v          # smoke Excel real
```

### Artefatos L2 (`data/l2/`)

| Artefato | Grain | Uso |
|----------|-------|-----|
| `train_features.parquet` | `data_processo` + `turno` | Treino Camada 3 |
| `holdout_features.parquet` | `data_processo` + `turno` | Matriz A (2025-05…10) |
| `infer_features.parquet` | `cenario_id` + `linha` | Inferência Modo B |
| `batch_manifest.json` | — | Rastreio, warnings, exclusions |
| `current.json` | — | Pointer last-good |

**Validação Excel real (2026-07-10):** 7.573 turnos lidos → 7.064 train + 500 holdout, `published_with_warnings`.

---

## 7. Estrutura do repositório

```text
src/ingest/           Código Camada 2 (I1–I5)
config/ingest.yaml    Paths, holdout, SLA online
tests/ingest/         Testes pytest
data/l2/              Artefatos publicados (gitignored)
docs/                 PRD, KB, diagramas
docs/diagrams/        Diagramas Mermaid (classes + fluxo ingest)
docs/kb/              Knowledge base normativa (gifi-ingest, gifi-domain)
excels/               Base QM×Processo 2018–2025
graphics/             Diagramas e imagens
.claude/sdd/archive/  Features SDD arquivadas
```

---

## 8. Documentação

| Documento | Conteúdo |
|-----------|----------|
| `docs/PRD_GIFI_v1.1.md` | Requisitos do produto |
| `docs/RESUMO_TECNICO_GIFI_v1.1.md` | Visão executiva e KPIs |
| `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | Protocolo de homologação (TC/TM) |
| `docs/sketch/ingest-engine.md` | Especificação macro do ingest |
| `docs/diagrams/INGEST_ENGINE.md` | Diagrama de classes + fluxo L2 |
| `docs/kb/gifi-ingest/` | Contratos YAML (colunas, sinais, warnings) |
| `docs/CHANGELOG.md` | Histórico de versões |
| `.claude/sdd/archive/INGEST_ENGINE/` | SDD shipped (DEFINE, DESIGN, BUILD) |

## 9. Escopo do MVP

**Dentro:** Ingest L2, cascata Elo 1→2→3, mix A/B/C, interface de simulação, explicabilidade assistida.  
**Fora:** Caminho da Volta, integração cloud em tempo real, RCA automática, retreino na UI, Redes Neurais (experimento opcional).

## 10. Pendências (Marco 2)

- Motor de Simulação (Camada 3) consumindo `data/l2/current.json`
- Testes E2E AT-011/012/014/017 (schema breaking, reprocess, determinismo, benchmark p95)
- Entrega da base interpolada pela TI (fallback: Excel consolidado)

---

*Projeto conduzido sob rastreabilidade documental. Alterações a decisões confirmadas exigem solicitação formal de mudança.*

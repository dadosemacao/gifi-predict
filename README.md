# GIFI — Simulador Preditivo de Produção de Celulose (TSA/dia)

**Autor:** Emerson Antônio (Cientista de Dados)
**Stakeholder:** Thiago Taglialegna Salles
**Time:** Keyrus | Veracel — Squad Sustentação
**Status:** Escopo consolidado (v1.1) — pronto para construção do MVP

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
|---|---|
| **A — Estatística** | `MAE ≤ 56 TSA/dia` no holdout temporal **2025-05 a 2025-10** (treino até 2025-04) |
| **B — Física** | Monotonicidade: DB↓, VMI↓, Extrativos↑, TPC<45, Carga↑ → TSA↓ |
| **C — Explicabilidade** | Top-3 detratores com contribuição em ΔTSA por cenário |

Release do MVP exige **A ∧ B ∧ C** (não intercambiáveis). Interface homologável até **31/08/2026**.

## 4. Parâmetros oficiais (evidência da base 2018–2025)

| Variável | Unidade | Ótima | Crítica |
|---|---|---|---|
| DB_LAB | kg/m³ | 470–510 | <450 ou >520 |
| Extrativo AT | % | 1,5–2,1 | >2,45 |
| TPC | dias | 60–90 | <45 (madeira verde) |
| Carga Alcalina | % Na₂O | 18,5–20,5 | >21,0 |
| Kappa | — | 16–18 | <15 ou >18,5 |

Imputação de densidade: `DB_LAB = 0,985 × DB_SGF` (fator legado 0,88 obsoleto).

## 5. Arquitetura (5 componentes)

`Domínio → Dados → Motor de Simulação → Confiança e Aceite → Superfície de Uso`

Diagrama: `graphics/mapa_componentes_gifi.png`

## 6. Documentação

| Documento | Conteúdo |
|---|---|
| `docs/PRD_GIFI_v1.1.md` | Requisitos do produto |
| `docs/RESUMO_TECNICO_GIFI_v1.1.md` | Visão executiva e KPIs |
| `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | Protocolo de homologação (TC/TM) |
| `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` | Faixas e limiares empíricos |
| `docs/sketch/DIVERGENCIAS_E_MITIGACAO_GIFI.md` | Divergências D-01…D-17 |
| `docs/sketch/DECOMPOSICAO_COMPONENTES_GIFI.md` | Fronteiras dos 5 componentes |
| `docs/sketch/MAPA_COMPONENTES_GIFI.md` | Mapa C0–C9 e ordem de construção |
| `docs/sketch/analytical-backbone.md` | Plano macro da plataforma determinística |
| `docs/sketch/ingest-engine.md` | Plano macro do sistema de ingestão |
| `docs/sketch/DECISOES_GIFI.md` | Registro de decisões |

## 7. Escopo do MVP

**Dentro:** cascata Elo 1→2→3, mix A/B/C, interface de simulação, explicabilidade assistida.
**Fora:** Caminho da Volta, integração cloud em tempo real, RCA automática, retreino na UI, Redes Neurais (experimento opcional).

## 8. Estrutura do repositório

```
docs/            requisitos, resumo, casos de teste
docs/sketch/     análises, planos e decisões
excels/          base de dados de referência (QM x Processo 2018-2025)
graphics/        diagramas e imagens
```

## 9. Pendências (não bloqueiam o build)

- Entrega da base interpolada pela TI (fallback: Excel consolidado).
- SLA de reprocesso quando a TI republicar a base.

---

*Projeto conduzido sob rastreabilidade documental. Alterações a decisões confirmadas exigem solicitação formal de mudança.*

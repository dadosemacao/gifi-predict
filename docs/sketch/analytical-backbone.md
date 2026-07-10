# Analytical Backbone — Plano Macro da Plataforma Determinística

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Versão:** 1.1  
**Escopo:** Camadas 1–5 (componentes de nível superior)  
**Brief de requisitos:** `docs/PRD_GIFI_v1.1.md`  
**Decomposição:** `docs/sketch/DECOMPOSICAO_COMPONENTES_GIFI.md`

---

## 1. O que é a plataforma determinística

Cadeia reproduzível e auditável do GIFI: **contrato → dados → cascata → aceite → uso**.  
“Determinística” aqui significa: mesmas entradas + mesmas regras → mesmas saídas intermediárias e finais; aceite por matrizes explícitas (não por julgamento ad hoc).

Fora deste plano: Caminho da Volta, cloud em tempo real, RCA automática, retreino na UI, NN (opcional pós-MVP).

---

## 2. Camadas e recursos

### Camada 1 — Domínio e Contrato

| Recurso | Função |
|---|---|
| Brief / PRD v1.1 | Escopo, alvo (TSA/dia), cascata, in/out |
| Faixas operacionais | Unidades, limiares, fator DB 0,985 |
| Protocolo de testes | Matrizes A/B/C e casos TC/TM |
| Template de cenário v0 | Contrato versionado de upload Modo A/B (`template_cenario_v0`) |
| Política de campeão | MAE + física + explicabilidade |

**Depende de:** —  
**Alimenta:** todas as camadas seguintes.

| Critério do brief | Relação |
|---|---|
| Escopo Caminho da Ida / sem lags | Congelado nesta camada |
| MAE ≤ 56; Matrizes B e C | Contratos definidos aqui |
| Faixas DB, Extrativos, TPC, Kappa | Referência normativa |

**Status:** pronto (docs v1.1).

---

### Camada 2 — Dados e Representação

| Recurso | Função |
|---|---|
| Ingestão + limpeza | Schema, filtro TSA < 1.000, imputação DB |
| Features de mix | Camadas A/B/C (`pct_*`, entropy, HHI, `dom_X`) |
| Qualidade ponderada | Médias por volume (DB, Extrativos, Casca) |
| Dataset versionado | Turno → dia, pronto para treino/inferência |

**Depende de:** Camada 1.  
**Alimenta:** Camadas 3 e 4.

| Critério do brief | Relação |
|---|---|
| Filtro < 1.000; unidade kg/m³; k=0,985 | Regras de limpeza |
| Mix A/B/C obrigatório | Features auditáveis |
| TC-08, TC-P01, TC-A02 | Aceite de representação |

---

### Camada 3 — Motor de Simulação (Caminho da Ida)

| Recurso | Função |
|---|---|
| Elo 1 | Sítio + Idade (+ mix) → Extrativo_AT |
| Elo 1b (opcional) | → % Casca |
| Elo 2 | Extrativo + TPC + DB_SGF → Carga |
| Elo 3 | Mix + qualidade + processo → TSA/dia |
| Modos A / B | Integração vs isolamento de elos |
| Baseline + EN + RF | Candidatos ao campeão |

**Depende de:** Camada 2 (+ contratos da Camada 1).  
**Alimenta:** Camadas 4 e 5 (inferência).

| Critério do brief | Relação |
|---|---|
| Cascata Elo 1→2→3 | Núcleo do motor |
| Reportar MAE por elo | Saídas intermediárias obrigatórias |
| Volume e Kappa no Elo 3 | Features de processo/escala |
| Política EN/RF (NN opcional) | Família de modelos do MVP |

---

### Camada 4 — Confiança e Aceite

| Recurso | Função |
|---|---|
| Matriz A | Holdout temporal; MAE ≤ 56; RMSE/WAPE |
| Matriz B | Monotonicidade / estresse físico (TC + TM) |
| Matriz C | Top-3 detratores (ΔTSA) |
| Seleção de campeão | Libera artefato só se A∧B∧C |

**Depende de:** Camadas 1, 2 e 3.  
**Alimenta:** Camada 5 (autorização de uso).

| Critério do brief | Relação |
|---|---|
| §4.3 Matriz A | Aceite estatístico |
| §4.3 Matriz B | Aceite físico |
| §4.3 Matriz C / §4.4 desvios | Explicabilidade assistida |
| Política de campeão | Gate de release |

---

### Camada 5 — Superfície de Uso

| Recurso | Função |
|---|---|
| Upload de cenário | Instância da planilha preenchida (validada contra template Camada 1) |
| Interface web | Upload → curvas TSA / Carga / Extrativos |
| Painel de detratores | Consumo da Matriz C |
| Relatório de aderência | Encerramento e gestão de desvios assistida |

**Depende de:** Camada 4 (release) + Camada 3 (inferência) + Camada 1 (template).  
**Alimenta:** — (MVP sem feedback loop).

| Critério do brief | Relação |
|---|---|
| §5 Interface (upload, curvas, top-3) | Escopo da UI |
| Homologação até 31/08/2026 | Marco da superfície mínima |
| Gestão de desvios assistida | Fluxo analista + decomposição |

---

## 3. Dependências (macro)

```
[1 Domínio] ──► [2 Dados] ──► [3 Motor] ──► [4 Confiança] ──► [5 Superfície]
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                    contratos / faixas / TCs
```

| Regra | Motivo |
|---|---|
| Sem 2 estável, não treinar 3 | Mesma representação em todos os elos |
| Sem 4, não homologar 5 | UI não substitui aceite |
| 1 permeia 2–5 | Evita regressão às divergências v1.0 |

---

## 4. Ordem de implementação

| Ordem | Camada | Entrega macro | Marco brief |
|---|---|---|---|
| 1 | Domínio | Contratos fechados | Feito |
| 2 | Dados | Dataset + features versionados | Marco 1 |
| 3 | Motor | Cascata + baseline + EN/RF | Marco 1–2 |
| 4 | Confiança | Matrizes A+B (mín.) → depois C | Marco 2–3 |
| 5 | Superfície | UI mínima → painel + relatório | Marco 2 (UI) / 4 (fechamento) |

**Caminho crítico até 31/08:** `2 → 3 → 4(A+B parcial) → 5(UI em modo demonstração)`.  
**Pós-31/08:** completar 4(C + B total) → 5(relatório) → go/no-go Elo 1b / NN.

> **Correção (obj. 2 — aceite):** “UI mínima” até 31/08 é entregue em **modo demonstração / homologação assistida**, sem release produtivo. O **release produtivo do MVP exige A ∧ B ∧ C completas** (`CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` §1.2 e §8). As matrizes **não são intercambiáveis**: `A+B parcial` habilita apenas testes internos, nunca uso operacional.

---

## 5. Critérios de aceite por camada (resumo)

| Camada | Pronto quando |
|---|---|
| 1 | Brief v1.1 + faixas + TCs publicados |
| 2 | Schema ok; mix soma 1; imputação 0,985; TC-P01/08/A02 |
| 3 | Modo A/B executável; MAE por elo reportado; candidatos EN/RF |
| 4 | MAE ≤ 56 **e** Matriz B **e** Matriz C |
| 5 | Upload + curvas + top-3; interface homologável |

Release do MVP = **Camada 4 completa** + **Camada 5 mínima**.

---

## 6. Decisões provisórias e pendências

> **Correção (obj. 2):** itens que são pré-condição de aceite deixam de ser “pendência aberta” e passam a ter **decisão provisória (default)** que **destrava a construção**. A decisão vale até confirmação formal do stakeholder; mudá-la depois é change request, não retrabalho estrutural.

### 6.1 Decisões provisórias (default para não bloquear build)

| Tema | Decisão | Status | Bloqueia build? |
|---|---|---|---|
| Janela de holdout temporal | **2025-05 a 2025-10** como holdout; treino em 2018-04→2025-04 | **Confirmada** (stakeholder, 2026-07-09) | Não |
| Elo 1b (% Casca) | **NO-GO no MVP**; casca só como feature Elo 3 quando medida | **Confirmada** (stakeholder, 2026-07-09) | Não |
| Agregação turno→dia | **Média ponderada por volume** (qualidade); **soma** (volume); TSA = **meta diária** | Assumida (CD) | Não |
| Template de cenário | Contrato é **artefato da Camada 1 (Domínio)**, versionado; UI consome (obj. 3) | Assumida (CD) | Não |

Registro completo: `DECISOES_GIFI.md`.

### 6.2 Pendências ainda abertas

| Pendência | Responsável | Bloqueia build? |
|---|---|---|
| Entrega TI da base interpolada | TI Veracel/Keyrus | Não (fallback: Excel consolidado) |
| SLA de reprocesso quando TI republicar base | TI + CD | Não |

---

## 7. Rastreio

| Documento | Papel |
|---|---|
| `PRD_GIFI_v1.1.md` | Brief / critérios de aceite |
| `DECOMPOSICAO_COMPONENTES_GIFI.md` | Fronteiras das 5 camadas |
| `MAPA_COMPONENTES_GIFI.md` | Detalhe C0–C9 |
| `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | Protocolo Matrizes B/C |
| Este arquivo | Plano macro da plataforma determinística |

---

*Nível macro apenas. Próximo passo: decompor cada camada em pacotes de trabalho — sem código nesta etapa.*

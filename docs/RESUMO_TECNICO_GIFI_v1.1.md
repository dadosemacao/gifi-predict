# Resumo Técnico — Projeto GIFI

**Versão:** 1.1  
**Data:** 2026-07-09  
**Autor:** Emerson Antônio (Cientista de Dados)  
**Stakeholder principal:** Thiago Taglialegna Salles  
**Status:** Alinhado ao PRD v1.1  
**Documentos irmãos:** `PRD_GIFI_v1.1.md`, `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`

---

## At a Glance — Painel Executivo

**Aviso crítico:** o planejamento de longo prazo (cenários 2025/2026) da Veracel fica limitado se a previsão de TSA/dia depender de **lags** (janelas móveis). Sem lags, é possível simular talhões ainda não cortados.

| Dimensão | Estado |
|---|---|
| Problema | Inconsistência entre qualidade da madeira planejada e TSA realizado |
| Solução MVP | Simulador preditivo **Caminho da Ida** (abastecimento → cascata → TSA) |
| Aceite estatístico | **MAE ≤ 56 TSA/dia** (holdout temporal **2025-05 a 2025-10**) |
| Aceite físico | Monotonicidade: DB↓, VMI↓, Extrativos↑, TPC verde, Carga↑ → TSA↓ |
| Aceite de gestão | Top-3 detratores explicáveis por cenário |
| Interface | Homologável até **31/08/2026** |

---

## 1. Problema e Impacto no Negócio

### 1.1 Problema executivo

O planejamento florestal e industrial enfrenta inconsistência crônica entre a qualidade da madeira planejada para abastecimento e o volume de celulose efetivamente produzido (TSA/dia).

Modelos anteriores usavam **lags**, criando autocorrelação artificial e impedindo simulações futuras onde a madeira ainda não foi cortada e não existem dados históricos imediatos.

Além disso, a operação carecia de método para isolar o impacto da madeira (extrativos, TPC verde, casca, densidade) das instabilidades mecânicas da planta.

### 1.2 Fluxo de impacto

```
Variáveis de abastecimento sem previsão limpa
        │
        ├── Dependência de lags → impossibilita cenários futuros
        ├── Inabilidade de isolar desvios (madeira vs. falha mecânica)
        │
        └── IMPACTOS
              ├── Operacional: quebra de consistência do digestor
              └── Financeiro: erros de projeção (estoques / compromissos)
```

### 1.3 Quem é afetado

| Área | Impacto |
|---|---|
| Planejamento Florestal | Não consegue testar preventivamente o mix (sítios A, B, C, D, MG) |
| Operações Industriais | Falta laudo estruturado: desvio veio da madeira ou da fábrica? |

---

## 2. Escopo do MVP 2026

### 2.1 In-Scope

| Item | Descrição |
|---|---|
| Caminho da Ida | Abastecimento → Extrativos → Carga → TSA |
| Remoção de lags | Simulações de longo prazo viáveis |
| Modelagem por turno → dia | Treino robusto; saída na meta diária |
| Interface simples | Upload manual de planilhas + curvas de projeção |
| Mix completo | A, B, C, D, MG + índices de diversidade |
| Explicabilidade assistida | Decomposição de detratores (não RCA automática) |

### 2.2 Out-of-Scope

| Item | Motivo |
|---|---|
| Caminho da Volta | Otimização reversa — Fase 2 |
| Integração automatizada Databricks/Azure | Complexidade fora do MVP |
| RCA automática / IA genética | Substituída por explicabilidade assistida |
| Retreino / feedback na UI | Fora do MVP |
| Redes Neurais obrigatórias | Apenas experimento opcional |

### 2.3 Estado atual vs. desejado

| Estado atual (Jul/2026) | Estado desejado (Ago–Set/2026) |
|---|---|
| Previsão presa a lags | Previsão limpa de longo prazo |
| Scripts isolados / planilhas manuais | Aplicação web unificada de simulação |
| Visão fragmentada lab × fábrica | Visão por turno consolidada na meta diária |
| MAE instável / sem validação física | MAE ≤ 56 + testes de consistência física |

---

## 3. Arquitetura Analítica (visão executiva)

```
Planejamento (mix, sítio, idade, TPC, volume, DB_SGF, Kappa)
        │
        ▼
   Elo 1  → Extrativo Álcool-Toluol
   Elo 1b → % Casca (NO-GO no MVP; casca = feature Elo 3 quando medida)
   Elo 2  → Carga Alcalina
   Elo 3  → TSA/dia
        │
        ▼
Interface: curva TSA + top-3 detratores
```

**Unidades oficiais:** densidade em **kg/m³**; extrativos em **%**; TPC em **dias**; volume em **m³**.

**Imputação DB:** `DB_LAB = 0,985 × DB_SGF` quando Lab ausente (fator legado 0,88 obsoleto).

**Limiares-chave (evidência 2018–2025):**

| Variável | Ótimo | Crítico |
|---|---|---|
| DB_LAB | 470–510 kg/m³ | <450 ou >520 |
| Extrativo AT | 1,5–2,1% | >2,45% |
| TPC | 60–90 dias | <45 (madeira verde) |
| Carga | 18,5–20,5% Na₂O | >21,0 |
| Kappa | 16–18 | <15 ou >18,5 |

Detalhamento completo: `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`.

---

## 4. Critérios de Aceitação Verificáveis e KPIs

Validação sob o stakeholder principal (Thiago Salles). Aceite exige **Matrizes A + B + C** (não intercambiáveis).

### 4.1 Aderência estatística (KPI: MAE)

| Critério | Contrato |
|---|---|
| MAE consolidado | **`MAE ≤ 56 TSA/dia`** no holdout temporal **2025-05 a 2025-10** (treino até 2025-04) |
| Auxiliares | RMSE e WAPE reportados |
| Cascata | `MAE_Extrativos`, `MAE_Carga`, `MAE_TSA` no relatório de aderência |

### 4.2 Consistência física (KPI: estresse de curva)

O algoritmo deve respeitar a física do processo. Em cenários simulados:

| Estímulo | Resposta compulsória |
|---|---|
| Queda forçada de Densidade Básica | Queda (ou não aumento) de TSA |
| Redução de VMI | Queda de TSA |
| Aumento de Extrativos | Queda de TSA |
| TPC < 45 dias | Queda de TSA |
| Aumento de Carga Alcalina | Queda de TSA |
| Diluição de mix seco (↑ pct_ABC) | Melhora de TSA vs. base |

Sinais empíricos de referência (subset com Extrativo AT):

| Par | ρ | Direção |
|---|---|---|
| Carga → TSA | −0,37 | detrator |
| TPC → TSA | +0,25 | verde piora |
| Extrativo AT → TSA | −0,13 | detrator |
| Casca → TSA | −0,15 | detrator |

### 4.3 Explicabilidade de detratores (KPI: assertividade de gestão)

| Critério | Contrato |
|---|---|
| Entregável | Top-3 atributos com contribuição em ΔTSA por cenário |
| Cobertura mínima | TPC (madeira jovem), Extrativo_AT, Carga Alcalina |
| Casca | Incluída quando medida (feature do Elo 3); Elo 1b NO-GO no MVP |
| Fora do MVP | Diagnóstico automático de causa raiz (RCA) |

### 4.4 Disponibilidade operacional (KPI: prazo)

Interface web funcional simplificada **disponível e homologada até 31 de agosto de 2026**.

---

## 5. Premissas em Aberto (atualizadas)

| Premissa | Status v1.1 | Mitigação |
|---|---|---|
| Erro composto da cascata não estoura MAE 56 | **Monitorada** | MAE por elo + Modos A/B de teste |
| Extrativo AT e % Casca estimados no longo prazo | **Parcial** | Elo 1 obrigatório; Elo 1b NO-GO no MVP; Casca no Elo 3 se medida |
| Representatividade logística (pilha / talhão→digestor) | **Mantida** | Premissa de negócio; monitorar viés por sítio |
| Foco exclusivo do recurso (4 h/dia) + escopo congelado | **Mantida** | Change request formal para novas demandas |
| Fator DB 0,985 | **Fechada pelos dados** | Reabrir só com evidência de processo contrária |

---

## 6. Cronograma Resumido

| Marco | Prazo | Entrega |
|---|---|---|
| 1 | Jul/2026 | Base limpa + baseline |
| 2 | 31/08/2026 | Modelos + interface homologável |
| 3 | Set/2026 | Validação temporal; NN opcional |
| 4 | Out–03/11/2026 | Estresse, relatório, encerramento |

---

## 7. Decisões de Escopo Consolidadas (v1.0 → v1.1)

| Tema | Decisão |
|---|---|
| Unidade de densidade | kg/m³ |
| Fator DB_LAB | 0,985 × DB_SGF |
| Extrativos | Ótimo ≤2,1%; crítico >2,45% |
| TPC verde | <45 dias |
| Kappa | Processo no Elo 3 (meta 16–18) |
| Volume | Feature de escala (faixa típica 6.000–11.000 m³) |
| Casca | Feature Elo 3 quando medida; Elo 1b NO-GO no MVP (confirmado) |
| MAE | ≤ 56 (não “próximo a”) |
| NN | Opcional |
| Gestão de desvios | Explicabilidade assistida |

---

## 8. Rastreabilidade

| Documento | Papel |
|---|---|
| `PRD_GIFI_v1.1.md` | Requisitos completos |
| Este resumo | Comunicação executiva e KPIs |
| `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | Protocolo de homologação |
| `sketch/DIVERGENCIAS_E_MITIGACAO_GIFI.md` | Histórico D-01…D-17 |
| `docs/CHANGELOG.md` | Histórico de versões do código |
| `docs/api/` | Dicionários das APIs REST (Camada 5) |
| `docs/sketch/MAPA_COMPONENTES_GIFI.md` | Status C0–C9 e backlog |

---

## 9. Addendum — estado de implementação (2026-07-13)

Documento normativo v1.1 permanece válido. Status técnico atual:

| Camada | Pacote | Status |
|--------|--------|--------|
| 2 — Ingest | `src/ingest/` | Shipped — imputação Extrativo_AT + `extr_origin` |
| 3 — Simulação | `src/simulation/` | Shipped — 13 preditores TSA (`process_specs.py`) |
| 4 — Aceite | `src/acceptance/` | Shipped MVP — `release_ok=false` (MAE ~89–97) |
| 5 — Serving + UI | `src/serving/` + `web/` | Shipped demo — cascata, forecast, what-if, audit SQLite |

**Produtos de inferência (Camada 5):** upload cascata (`/api/simulate`), forecast operacional (`/api/forecast`), what-if direto (`/api/predict-tsa`).

**Próximo marco:** gate A∧B∧C verde + homologação produtiva da UI (`demo=false`).

---

*Resumo Técnico v1.1 — reconstruído com integridade a partir do PDF original, da base QM×Processo e do PRD v1.1. Addendum §9 sincronizado em 2026-07-13.*

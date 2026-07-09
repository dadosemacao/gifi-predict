# Mapa de Componentes e Dependências — Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 1.0  
**Base normativa:** `PRD_GIFI_v1.1.md`, `RESUMO_TECNICO_GIFI_v1.1.md`, `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`  
**Objetivo:** visão única para decompor o sistema em tarefas de construção.

---

## 1. Visão em uma frase

O GIFI é um **simulador preditivo em cascata** (Caminho da Ida): dados de planejamento florestal → features de mix/qualidade → Elo 1 (Extrativos) → Elo 2 (Carga) → Elo 3 (TSA/dia) → interface + explicabilidade, validado por três matrizes de aceite (MAE, física, detratores).

---

## 2. Mapa de camadas

```
L0  Fundação documental + base bruta
L1  Dados limpos + engenharia de features
L2  Cascata preditiva (Elo 1 → 1b → 2 → 3)
L3  Validação e seleção de modelo (Matrizes A/B/C)
L4  Produto (interface + relatório de desvios)
```

Diagrama: `graphics/mapa_componentes_gifi.png`

---

## 3. Componentes principais

### C0 — Fundação documental

| Item | Conteúdo |
|---|---|
| **O que é** | PRD, Resumo, Casos de Teste, Faixas Operacionais |
| **Entrega** | Contratos de escopo, faixas, KPIs, protocolo de homologação |
| **Depende de** | — (já consolidado na v1.1) |
| **Bloqueia** | Qualquer implementação sem referência numérica |
| **Status** | **Pronto** |

---

### C1 — Ingestão e limpeza de dados

| Item | Conteúdo |
|---|---|
| **O que é** | Pipeline que lê a base QM×Processo, tipa colunas, aplica filtros e imputações |
| **Regras-chave** | Unidade kg/m³; filtro TSA < 1.000; `DB_LAB = 0,985 × DB_SGF` se Lab ausente; soma mix ≈ 1,0 |
| **Entradas** | Excel consolidado 2018–2025 (+ tabelas limpas da TI, quando disponíveis) |
| **Saídas** | Dataset de treino/validação versionado (turno → dia) |
| **Depende de** | C0 (faixas/schema) |
| **Bloqueia** | C2, C3…C6 |
| **Status** | **Pendente** — base bruta existe; pipeline ainda não construído |

---

### C2 — Engenharia de features (Mix A/B/C + qualidade)

| Item | Conteúdo |
|---|---|
| **O que é** | Camada analítica: percentuais, compostos, diversidade, médias ponderadas |
| **Features** | `pct_*`, `pct_ABC`, `pct_CDMG`, `mix_entropy`, `mix_hhi`, `dom_X`, DB/Extrativos/Casca ponderados, VMI, TPC, Volume, Kappa |
| **Depende de** | C1 |
| **Bloqueia** | C3, C4, C5, C6 |
| **Testes associados** | TC-08, TC-P01, TC-A02 |
| **Status** | **Pendente** |

---

### C3 — Elo 1: Extrativo Álcool-Toluol

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo que estima Extrativo_AT a partir de Sítio + Idade (+ mix) |
| **Saída** | `Extrativo_AT` estimado |
| **Depende de** | C2 |
| **Bloqueia** | C5 (Elo 2), parcialmente C6 |
| **Métrica** | `MAE_Extrativos` (reportar; não bloqueia sozinho o aceite global) |
| **Risco** | Cobertura Lab forte só a partir de ~2024 |
| **Status** | **Pendente** |

---

### C3b — Elo 1b: % Casca (opcional MVP+)

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo auxiliar Sítio + Idade → % Casca |
| **Depende de** | C2 |
| **Bloqueia** | Explicabilidade com casca; não bloqueia MVP mínimo do Elo 3 se Casca medida existir |
| **Decisão** | Incluir se viável; senão Casca só como feature quando disponível |
| **Status** | **Pendente / escopo opcional** |

---

### C4 — Elo 2: Carga Alcalina

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo Extrativo_AT + TPC + DB_SGF → Carga Alcalina |
| **Depende de** | C2 + C3 (no Modo A); no Modo B aceita Extrativo injetado |
| **Bloqueia** | C5 (Elo 3 no Modo A) |
| **Métrica** | `MAE_Carga` |
| **Status** | **Pendente** |

---

### C5 — Elo 3: TSA/dia (modelo campeão)

| Item | Conteúdo |
|---|---|
| **O que é** | Modelo final de produção: mix + qualidade + processo → TSA/dia |
| **Algoritmos** | Baseline → ElasticNet → Random Forest (NN opcional depois) |
| **Depende de** | C2 + C4 (+ C3/C3b no Modo A) |
| **Bloqueia** | C6, C7, C8 |
| **KPI** | `MAE_TSA ≤ 56` + monotonicidade física |
| **Status** | **Pendente** |

---

### C6 — Validação e seleção (Matrizes A/B/C)

| Item | Conteúdo |
|---|---|
| **O que é** | Protocolo de aceite e escolha do modelo campeão |
| **Matriz A** | Holdout temporal; MAE ≤ 56 |
| **Matriz B** | TC-01…08 + TM-01…05 (física) |
| **Matriz C** | TC-09/10 (top-3 detratores) |
| **Depende de** | C3, C4, C5 (+ artefatos de explicabilidade) |
| **Bloqueia** | Release da interface e relatório final |
| **Status** | **Especificado; execução pendente** |

---

### C7 — Explicabilidade e gestão de desvios

| Item | Conteúdo |
|---|---|
| **O que é** | Decomposição de impacto (SHAP/importância) → top-3 detratores |
| **Depende de** | C5 (modelo campeão) |
| **Bloqueia** | Matriz C e painel da UI |
| **Fora** | RCA automática |
| **Status** | **Pendente** |

---

### C8 — Interface web do simulador

| Item | Conteúdo |
|---|---|
| **O que é** | Upload de planilha → execução Modo A/B → curvas TSA + Carga + Extrativos + top-3 |
| **Depende de** | C5 + C6 (mínimo funcional) + C7 (para homologação completa) |
| **Prazo** | Homologável até **31/08/2026** |
| **Fora** | Retreino na UI, cloud, Caminho da Volta |
| **Status** | **Pendente** |

---

### C9 — Relatório de aderência e encerramento

| Item | Conteúdo |
|---|---|
| **O que é** | Documentação de métricas, estresse físico, limitações, versão do modelo |
| **Depende de** | C6 + C7 + C8 |
| **Prazo** | Marco 4 (até 03/11/2026) |
| **Status** | **Pendente** |

---

## 4. Grafo de dependências (ordem lógica)

```
C0 Docs ──┐
          ├──► C1 Limpeza ──► C2 Features ──┬──► C3 Elo1 ──► C4 Elo2 ──┐
C_raw ────┘                                 ├──► C3b Elo1b (opc.) ────┼──► C5 Elo3
                                            └─────────────────────────┘
                                                      │
                                                      ▼
                                              C6 Validação A/B/C
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                                 C7 Explain        C8 UI             (release)
                                    └────────┬────────┘
                                             ▼
                                          C9 Relatório
```

**Regra:** não iniciar C5 sem C2 estável; não homologar C8 sem Matriz B mínima; não encerrar sem C6+C7+C9.

---

## 5. Ordem de construção recomendada

| Ordem | Componente | Marco sugerido | Critério para avançar |
|---|---|---|---|
| **1** | C0 Docs | Feito | v1.1 publicada |
| **2** | C1 Limpeza + schema | Marco 1 | Dataset versionado; TC-P01 / TC-A02 verdes |
| **3** | C2 Features Mix A/B/C | Marco 1 | TC-08 verde; soma mix = 1 |
| **4** | Baseline Elo 3 (sem cascata completa) | Marco 1 | Baseline MAE documentado |
| **5** | C3 Elo 1 | Marco 2 | `MAE_Extrativos` reportado |
| **6** | C4 Elo 2 | Marco 2 | `MAE_Carga` reportado |
| **7** | C5 Elo 3 (ElasticNet + RF) | Marco 2 | Candidatos prontos para Matriz A |
| **8** | C6 Matriz A + B (parcial) | Marco 2 | MAE ≤ 56 **ou** plano de gap; TC físicos críticos Pass |
| **9** | C8 UI mínima (upload + TSA) | Marco 2 (31/08) | Simulação Modo A funcional |
| **10** | C7 Explicabilidade | Marco 2–3 | Top-3 por cenário |
| **11** | C6 Matriz C + B completa | Marco 3 | TC-09/10 + TM-01…05 |
| **12** | C3b Casca (se viável) | Marco 3 | Decisão go/no-go |
| **13** | NN opcional | Marco 3 | Só se vencer A+B+C |
| **14** | C9 Relatório final | Marco 4 | Encerramento |

---

## 6. Dependências externas (fora do código)

| Dependência | Dono | Impacto se atrasar |
|---|---|---|
| Tabelas analíticas limpas / interpoladas (TI) | TI Veracel/Keyrus | Atrasa C1; PRD prevê ganho de ~22 dias se entregue |
| Validação de faixas com processo (se reabrir 0,88) | Stakeholder / Processo | Baixo — valores já otimizados pelos dados |
| Template oficial de planilha de cenário | CD + negócio | Bloqueia C8 e homologação |
| Definição do holdout temporal exato (2025 vs “2026”) | CD + stakeholder | Afeta Matriz A |

---

## 7. Pontos ainda pendentes

### Bloqueantes para começar a construir

1. **Pipeline C1/C2 inexistente** — há Excel de referência, não há código/dataset versionado no repositório.
2. **Protocolo de holdout temporal** — PRD cita 2026; base vai até out/2025. Precisa fechar a janela de teste (ex.: últimos N meses de 2025) antes da Matriz A.
3. **Template de planilha de cenário** — contrato de colunas Modo A vs Modo B ainda não materializado em arquivo.

### Decisões de escopo em aberto (não bloqueiam o início)

4. **Elo 1b (% Casca)** — go/no-go após C2; MVP pode seguir com Casca só quando medida.
5. **Redes Neurais** — explícito como opcional; não entra no caminho crítico.
6. **Agregação turno→dia** — regra de agregação (média, soma, turno representativo) precisa ser fixada em C1.

### Riscos técnicos a monitorar

7. **Erro composto da cascata** — maior ameaça ao MAE 56; exige MAE por elo desde C3/C4.
8. **Cobertura de Extrativo_AT** — esparsa antes de 2024; Elo 1 pode ser frágil fora desse período.
9. **Sítios D/MG** — poucos casos de dominância; testes serão majoritariamente sintéticos.
10. **Entrega TI da base interpolada** — se não vier, C1 consome esforço extra de preparação.

### Explicitamente fora do MVP (não pendência de construção)

- Caminho da Volta  
- Integração Databricks/Azure em tempo real  
- RCA automática  
- Retreino/feedback na UI  

---

## 8. Pacotes de trabalho (prévia para o backlog)

| Pacote | Componentes | Resultado |
|---|---|---|
| **P1 — Dados** | C1 + C2 | Dataset + features auditáveis |
| **P2 — Cascata** | C3 + C4 + C5 | Modelos encadeados + baseline |
| **P3 — Aceite** | C6 + C7 | Matrizes A/B/C + explicabilidade |
| **P4 — Produto** | C8 + template | Simulador homologável |
| **P5 — Fechamento** | C9 (+ C3b/NN se go) | Relatório e encerramento |

Próximo passo natural: quebrar **P1→P5** em tarefas com dono, estimativa e DoD.

---

*Documento de planejamento técnico. Serve como SSOT para decomposição de tarefas do MVP GIFI.*

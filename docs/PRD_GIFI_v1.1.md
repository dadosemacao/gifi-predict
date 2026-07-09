# Documento de Requisitos do Produto (PRD) — Projeto GIFI

**Versão:** 1.1  
**Data:** 2026-07-09  
**Autor:** Emerson Antônio (Cientista de Dados)  
**Stakeholder principal:** Thiago Taglialegna Salles  
**Time:** Emerson Antônio + Squad Sustentação (Keyrus | Veracel)  
**Status:** Escopo alinhado — Marco Zero consolidado  
**Base de evidência:** `excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx`  
**Documentos irmãos:** `RESUMO_TECNICO_GIFI_v1.1.md`, `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`

---

## 0. Controle de Mudanças (v1.0 PDF → v1.1)

| ID | Lacuna / divergência | Resolução nesta versão |
|---|---|---|
| D-01 | Faixas DB conflitantes | Ótima 470–510 kg/m³; crítica <450 ou >520 |
| D-02 | Unidade g/cm³ vs kg/m³ | Unidade oficial **kg/m³** (confirmada na base) |
| D-03 | Extrativos contraditórios | Ótima 1,5–2,1%; crítica >2,45% |
| D-04 | Estresse físico incompleto | Inclui DB, VMI, Extrativos, TPC, Mix, Carga |
| D-05 | % Casca ausente | Elo 1b **NO-GO no MVP** (confirmado); casca = feature Elo 3 quando medida; explicabilidade assistida |
| D-06 | Cascata vs injeção nos testes | Modos A (integração) e B (isolamento) definidos |
| D-07 | DB_SGF vs DB_LAB / fator 0,88 | Fator **0,985**; diagrama de conversão por elo |
| D-08 | Kappa ausente | Kappa 16–18 como processo fixo/estimado no Elo 3 |
| D-09 | Sítios D/MG sem teste | Cobertura obrigatória no plano de testes |
| D-10 | Camada C sem validação | Requisitos + testes unitários de features |
| D-11 | Explicabilidade sem entregável | Top-3 detratores com ΔTSA por cenário |
| D-12 | RCA vs gestão de desvios | MVP = explicabilidade assistida (não RCA automática) |
| D-13 | MAE “próximo a 56” | Contrato: **MAE_holdout ≤ 56 TSA/dia** |
| D-14 | Limiar TPC verde | **TPC < 45 dias** = madeira verde |
| D-15 | Redes Neurais | Experimento opcional; não bloqueia MVP |
| D-16 | Volume_m3 | Feature de escala no Elo 3; faixa 6.000–11.000 m³ |
| D-17 | Filtro <1.000 | Regra de treino + teste de pipeline |

---

## 1. Visão Geral e Objetivos de Negócio

### 1.1 Contexto

O planejamento florestal e industrial da Veracel precisa estimar a produção real de celulose (**TSA/dia**) em cenários de longo prazo (planejamentos 2025/2026). Modelos anteriores dependiam de variáveis históricas imediatas (**lags** / janelas móveis), o que inviabiliza simulações em talhões ainda não cortados.

### 1.2 Framing analítico

| Dimensão | Definição |
|---|---|
| **Variável-alvo** | Produção digestor (TSA/dia), consolidada por turno e agregada na meta diária |
| **Horizonte** | Simulação de cenários futuros de abastecimento |
| **Entradas** | Mix por sítio (A, B, C, D, MG), qualidade ponderada por volume, processo fixo ou estimado |
| **Restrição** | Exclusão total de lags |
| **Decisão** | Ajustar frentes de colheita e mix com base na TSA estimada |
| **Uso secundário** | Isolar desvios planejado × estimado × realizado (madeira vs. fábrica) |

### 1.3 Objetivos práticos

1. **Modelo de previsão:** estimar TSA/dia apenas com variáveis de planejamento de abastecimento e dados fixos/estimados de processo.
2. **Simulador de cenários (Caminho da Ida):** upload de planilha de mix → estimativa física de produção.
3. **Gestão de desvios (assistida):** decomposição de impacto dos atributos (explicabilidade), sem RCA automática por IA.

---

## 2. Escopo do MVP (Fase 1)

### 2.1 In-Scope

| Item | Descrição |
|---|---|
| Caminho da Ida | Fluxo exclusivo: Abastecimento → (cascata) → TSA |
| Sem lags | Remoção total de janelas móveis / autocorrelação temporal |
| Modelagem híbrida | Baseline + ElasticNet + Random Forest Regressor |
| Interface web local | Upload de planilhas de cenário e curvas de produção estimada |
| Agregação | Dados por turno industrial → meta diária |
| Mix completo | Sítios A, B, C, D, MG + Camadas A/B/C de features |
| Cascata | Elo 1 (Extrativos), Elo 2 (Carga), Elo 3 (TSA); Elo 1b (Casca) = NO-GO no MVP |
| Explicabilidade assistida | Top-3 detratores com contribuição em ΔTSA |

### 2.2 Out-of-Scope

| Item | Observação |
|---|---|
| Caminho da Volta | Otimização reversa (TSA alvo → mix ideal) — Fase 2 |
| Integração TI em tempo real | Databricks / Azure automáticos — fora do MVP |
| Retreino / feedback na UI | Botões de retreino, curtidas — fora do MVP |
| RCA automática / IA genética | Fora do MVP; substituída por explicabilidade assistida |
| Redes Neurais como entrega obrigatória | Apenas experimento opcional (Marco 3) |

---

## 3. Requisitos de Dados e Engenharia de Atributos

### 3.1 Fonte e granularidade

| Item | Valor |
|---|---|
| Fonte de referência | Base QM × Processo 2018–2025 consolidada |
| Granularidade de treino | Turno industrial |
| Saída de negócio | TSA/dia (agregação diária) |
| Período histórico disponível | 2018-04 a 2025-10 |

### 3.2 Filtros e limpeza

| Regra | Especificação |
|---|---|
| Filtro operacional | Excluir do treino registros com `Produção_Digestor < 1.000 TSA/dia` |
| Unidade de densidade | **kg/m³** (obrigatório) |
| Schema DB | Alertar se `DB_LAB` ou `DB_SGF` ∉ [350, 650] |
| Imputação DB_LAB ausente | **`DB_LAB = 0,985 × DB_SGF`** (fator otimizado na base; MAE ≈ 12 kg/m³). O fator legado 0,88 está **obsoleto**. |
| Mix | `pct_A + pct_B + pct_C + pct_D + pct_MG = 1,0` (tolerância ±0,02) |

### 3.3 Camadas do mix de abastecimento

#### Camada A — Percentuais absolutos

`pct_A`, `pct_B`, `pct_C`, `pct_D`, `pct_MG` (soma diária = 1,0).

#### Camada B — Variáveis compostas

| Feature | Definição |
|---|---|
| `pct_ABC` | `pct_A + pct_B + pct_C` (crescimento rápido) |
| `pct_CDMG` | `pct_C + pct_D + pct_MG` (madeiras secas/densas) |

#### Camada C — Diversidade e controle

| Feature | Definição |
|---|---|
| `mix_entropy` | Entropia de Shannon do mix |
| `mix_hhi` | Índice Herfindahl-Hirschman (concentração) |
| `dom_X` | Flag 1 se `pct_X > 0,50` (X ∈ {A,B,C,D,MG}) |

### 3.4 Qualidade ponderada por volume

Fórmula obrigatória:

```
média_ponderada = Σ (valor_i × volume_i) / Σ volume_i
```

Variáveis ponderadas: `DB_LAB`, `Extrativo_AT`, `% Casca` (quando disponível), demais atributos de qualidade do abastecimento.

### 3.5 Faixas operacionais oficiais

Fonte: `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` (evidência empírica 2018–2025).

| Variável | Unidade | Ótima | Aceitável | Crítica | Âncora (p50) |
|---|---|---|---|---|---|
| DB_LAB | kg/m³ | 470–510 | 450–470 / 510–520 | <450 ou >520 | 483 |
| DB_SGF | kg/m³ | 475–505 | 465–475 / 505–515 | <465 ou >515 | 490 |
| Extrativo AT | % | 1,5–2,1 | 2,1–2,45 | >2,45 | 1,89 |
| TPC | dias | 60–90 | 45–60 | <45 (verde) | 65 |
| Carga Alcalina | % Na₂O | 18,5–20,5 | 17,5–21,0 | >21,0 ou <17,5 | 19,66 |
| Kappa | — | 16–18 | 15–18,5 | <15 ou >18,5 | 16,28 |
| % Casca | % | ≤1,0 | 1,0–1,5 | >1,5 | 0,80 |
| VMI | m³ | >0,25 | 0,21–0,25 | ≤0,21 | 0,25 |
| Volume | m³ | 7.500–9.500 | 6.000–11.000 | <6.000 | 8.669 |
| TSA | TSA/dia | 3.350–3.500 | 3.200–3.600 | <3.200* | 3.450 |

\*Em operação contínua; paradas <1.000 ficam fora do treino.

### 3.6 Variáveis de processo no Elo 3

| Variável | Papel no MVP |
|---|---|
| **Kappa** | Processo fixo ou estimado pelo usuário no cenário; meta 16–18; **não** gerado pela cascata florestal |
| **Volume abastecido** | Feature de escala no Elo 3 (além da ponderação de qualidade) |
| **Carga Alcalina** | Saída do Elo 2 (estimada) ou injetada no Modo B de teste |
| **% Casca** | Feature do Elo 3 quando medida. **Elo 1b (estimativa automática) = NO-GO no MVP** — decisão confirmada (ver `sketch/DECISOES_GIFI.md`, D-B); reavaliar na Fase 2 |

---

## 4. Requisitos Funcionais do Modelo Preditivo

### 4.1 Cascata de estimação (Caminho da Ida)

```
[Entrada planejamento]
   Sítio + Idade + Mix + TPC + Volume + DB_SGF (+ Kappa fixo)
        │
        ├─ Elo 1:  Sítio + Idade (+ mix) → Extrativo_AT
        ├─ Elo 1b (NO-GO no MVP; Fase 2): Sítio + Idade → % Casca
        │
        ├─ Elo 2: Extrativo_AT + TPC + DB_SGF → Carga Alcalina
        │
        └─ Elo 3: Mix (A/B/C) + DB_LAB* + Extrativo + Carga + TPC
                  + VMI + Volume + Kappa (+ Casca se houver)
                  → TSA/dia

* DB_LAB = medida Lab, ou 0,985 × DB_SGF se Lab ausente
```

#### Modos de execução

| Modo | Uso | Entradas do usuário |
|---|---|---|
| **A — Integração** | Simulação de longo prazo / homologação end-to-end | Sítio, Idade, Mix, TPC, Volume, DB_SGF, Kappa; Extrativos e Carga **estimados** |
| **B — Isolamento** | Diagnóstico de elos / testes de estresse | Permite injetar Extrativo_AT, Carga, DB_LAB medidos |

### 4.2 Algoritmos e política de seleção

| Etapa | Modelo | Obrigatoriedade |
|---|---|---|
| Baseline | Média / regressão linear simples | Obrigatório |
| MVP | ElasticNet + Random Forest Regressor | Obrigatório |
| Experimento | Redes Neurais | Opcional (Marco 3); só vira campeão se vencer Matrizes A+B+C |

**Política de campeão:** melhor MAE_holdout **desde que** passe consistência física e explicabilidade mínima. Em empate: interpretabilidade > complexidade.

### 4.3 Critérios de aceite (KPIs)

#### Matriz A — Estatística

| KPI | Contrato |
|---|---|
| MAE holdout | **`MAE ≤ 56 TSA/dia`** no holdout temporal **2025-05 a 2025-10** (treino até 2025-04); decisão confirmada pelo stakeholder (ver `sketch/DECISOES_GIFI.md`, D-A). A meta original citava 2026, inexistente na base (até out/2025) |
| Métricas auxiliares | Reportar RMSE e WAPE no relatório de aderência |
| MAE por elo | Reportar `MAE_Extrativos`, `MAE_Carga`, `MAE_TSA` (não bloqueiam sozinhos o aceite global, mas são obrigatórios no relatório) |

#### Matriz B — Consistência física (obrigatória)

Em testes de estresse / monotonicidade, com demais variáveis fixas:

| Estímulo | Resposta obrigatória |
|---|---|
| DB_LAB ↓ | TSA ↓ (ou não sobe) |
| VMI ↓ | TSA ↓ |
| Extrativo_AT ↑ | TSA ↓ |
| TPC < 45 (e ↓) | TSA ↓ |
| Carga Alcalina ↑ | TSA ↓ |
| Mix diluidor (↑ pct_ABC sobre base seca C) | TSA ↑ vs. cenário base |

#### Matriz C — Explicabilidade

| Entregável | Critério |
|---|---|
| Por cenário | Top-3 detratores com contribuição estimada em ΔTSA |
| Detratores mínimos cobertos | TPC (madeira verde), Extrativo_AT, Carga Alcalina; Casca quando feature ativa |
| Método | Importância de atributos / SHAP / decomposição equivalente documentada |

### 4.4 Gestão de desvios (MVP)

Fluxo:

1. Usuário informa período ou cenário com desvio (planejado × estimado × realizado).
2. Sistema retorna decomposição dos atributos.
3. Analista interpreta (sem RCA automática).

---

## 5. Requisitos da Interface

| Requisito | Detalhe |
|---|---|
| Upload | Planilha de cenários (template oficial) |
| Saídas | Curva / tabela de TSA estimada; Carga estimada (Elo 2); Extrativos estimados (Elo 1) |
| Explicabilidade | Painel ou relatório com top-3 detratores |
| Ambiente | Aplicação local / web simples |
| Fora | Retreino, feedback social, integração cloud |

**Prazo de disponibilidade operacional:** interface homologável até **31 de agosto de 2026** (Marco 2).

---

## 6. Cronograma e Marcos

Premissa: dedicação parcial (~4 h/dia); ciclos de monitoramento a cada 15 dias; escopo congelado.

| Marco | Prazo | Entrega |
|---|---|---|
| **1** | Julho/2026 | Base interpolada + tabelas limpas (TI) + baseline MVP |
| **2** | 31/08/2026 | ElasticNet/RF com mix; interface para testes de cenário; início da Matriz B |
| **3** | Setembro/2026 | Validação cruzada temporal; congelamento de hiperparâmetros; NN opcional |
| **4** | Outubro–03/11/2026 | Estresse físico, relatório de aderência, documentação, encerramento |

---

## 7. Premissas e Riscos

| Premissa / risco | Mitigação |
|---|---|
| Erro composto da cascata pode estourar MAE 56 | MAE por elo + Modos A/B + relatório de propagação |
| Extrativo AT com cobertura histórica parcial (forte a partir de 2024) | Elo 1 treinado no período com Lab; validar estabilidade |
| Aproximação logística (pilha / rastreio talhão→digestor) | Premissa de representatividade; monitorar viés por sítio |
| Escopo congelado | Premissa de prazo; mudanças passam por change request |
| Fator 0,985 vs. legado 0,88 | Adotar 0,985; stakeholder só reabre se houver razão de processo documentada |

---

## 8. Rastreabilidade

| Artefato | Papel |
|---|---|
| Este PRD v1.1 | Requisitos oficiais do produto |
| `RESUMO_TECNICO_GIFI_v1.1.md` | Visão executiva e KPIs |
| `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | Homologação Matrizes B e C |
| `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` | Faixas e limiares empíricos |
| `sketch/DIVERGENCIAS_E_MITIGACAO_GIFI.md` | Histórico de conflitos D-01…D-17 |

---

*PRD v1.1 — reconstruído com integridade documental a partir dos PDFs originais, da base QM×Processo e da análise de divergências.*

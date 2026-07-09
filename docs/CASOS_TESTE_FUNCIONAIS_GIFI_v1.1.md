# Casos de Testes Funcionais e Homologação — Projeto GIFI

**Versão:** 1.1  
**Data:** 2026-07-09  
**Autor:** Emerson Antônio (Cientista de Dados)  
**Stakeholder:** Thiago Taglialegna Salles  
**Ambiente:** Interface Web do Simulador (MVP)  
**Documentos irmãos:** `PRD_GIFI_v1.1.md`, `RESUMO_TECNICO_GIFI_v1.1.md`, `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`

---

## 0. Controle de Mudanças (v1.0 PDF → v1.1)

| Lacuna | Correção |
|---|---|
| Unidade g/cm³ | Padronizado para **kg/m³** |
| DB “crítico 490” / ótimo 400–500 | Faixas oficiais: ótima 470–510; TC-03 usa **455** |
| Extrativos teto 1,5% / 2,0% | Ótimo ≤2,1%; crítico >2,45% |
| Volume 1.050 / 1.200 | Escala real **~6.000–11.000 m³** |
| Carga “>22%” | Crítico **>21,0%** (máx. histórico ≈21,95) |
| Só sítios A/B/C | Incluídos TC-06 (D), TC-07 (CDMG), TC-08 (Camada C) |
| Sem teste de cascata / explicabilidade | Modos A/B + TC-09 / TC-10 |
| Sem teste de pipeline | TC-P01 (filtro <1.000) |
| ρ citados sem base | Usar ρ da referência operacional até reestimar no pipeline |

---

## 1. Diretrizes de Execução

### 1.1 Ambiente e massa

| Item | Valor |
|---|---|
| Ambiente | Interface Web do Simulador (MVP) |
| Massa | Planilhas de cenário com valores fixados (template oficial) |
| Unidade de densidade | **kg/m³** (nunca g/cm³) |
| Referência de faixas | `sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` |

### 1.2 Matrizes de aceite (obrigatórias e não intercambiáveis)

| Matriz | Escopo | Critério de sucesso |
|---|---|---|
| **A — Estatística** | Holdout temporal | `MAE ≤ 56 TSA/dia` |
| **B — Comportamental** | TC-01…TC-08 + monotonicidades | 100% Pass na direção física |
| **C — Explicabilidade** | TC-09, TC-10 | Detratores corretos no top-3 |

### 1.3 Modos de teste da cascata

| Modo | Quando usar | Entradas |
|---|---|---|
| **A — Integração** | Validar Elo 1→2→3 end-to-end | Sítio, Idade, Mix, TPC, Volume, DB_SGF, Kappa; Extrativos/Carga **estimados** |
| **B — Isolamento** | Isolar efeito de uma variável | Permite injetar Extrativo_AT, Carga, DB_LAB |

Cada caso abaixo declara o modo.

### 1.4 Critério geral

O simulador deve responder de forma fisicamente consistente e, no conjunto estatístico, respeitar **MAE ≤ 56 TSA/dia**. Testes funcionais **não substituem** o holdout da Matriz A.

---

## 2. Matriz de Casos por Sítio Florestal

### TC-01 — Escala no Sítio A (Úmido)

| Campo | Valor |
|---|---|
| Objetivo | Verificar resposta estável e produção elevada com Sítio A dominante e alto volume |
| Modo | B (isolamento) |
| Entrada | `pct_A = 1,0`; Volume ≥ **10.000 m³**; `DB_LAB = 480 kg/m³`; `TPC = 75`; `Extrativo_AT = 1,8%`; Kappa = 17,0 |
| Esperado Elo 2 | Carga Alcalina **≤ 19,5%** Na₂O (baixa/otimizada) |
| Esperado Elo 3 | TSA em patamar elevado e estável (referência histórica A dominante ≈ 3.430+ TSA/dia) |
| Não esperado | Queda severa de TSA sem estímulo de detrator |

### TC-02 — Equilíbrio no Sítio B (Intermediário)

| Campo | Valor |
|---|---|
| Objetivo | Validar equilíbrio florestal × industrial |
| Modo | B |
| Entrada | `pct_B = 1,0` (cenário sintético; B≥0,95 é raro na base); Volume ≈ **8.600 m³**; `DB_LAB = 483 kg/m³`; `TPC = 65`; Kappa = **17,0** |
| Esperado Elo 2 | Carga Alcalina entre **19% e 21%** Na₂O |
| Esperado Elo 3 | TSA alinhada ao baseline histórico de B dominante (≈ 3.390–3.450) |
| Nota | Kappa é **pré-condição / feature de processo**, não saída do Elo 2 |

### TC-03 — Estresse crítico no Sítio C (Seco)

| Campo | Valor |
|---|---|
| Objetivo | Garantir penalização em zona de restrição (não gerar meta irreal) |
| Modo | B |
| Entrada | `pct_C = 1,0`; `DB_LAB = 455 kg/m³` (≈p05; zona crítica/baixa); `Extrativo_AT = 2,6%` (>2,45 crítico); Kappa = 18,0 |
| Esperado Elo 2 | Carga Alcalina **> 21,0%** Na₂O (crítica alta; não exigir >22%) |
| Esperado Elo 3 | **Queda clara** de TSA vs. TC-01/TC-02 |
| Sinais de referência | Carga→TSA ρ≈−0,37; Extrativo→TSA ρ≈−0,13 (base 2018–2025) |

---

## 3. Testes Inter-Sítios, Mix e TPC

### TC-04 — Amortecimento químico via mix

| Campo | Valor |
|---|---|
| Objetivo | Diluir frente severa (C) com fatias estabilizadoras |
| Modo | B |
| Base | `pct_C = 1,0`; Extrativo_AT = **2,2%** |
| Testado | `pct_C = 0,40`; `pct_A = 0,40`; `pct_B = 0,20` → `pct_ABC = 1,0` |
| Esperado | Extrativo ponderado ↓; Carga ↓; **TSA ↑** vs. cenário base |

### TC-05 — Madeira verde (baixo TPC)

| Campo | Valor |
|---|---|
| Objetivo | Penalizar rendimento quando TPC viola limiar de pátio |
| Modo | B |
| Entrada | `pct_ABC = 1,0`; `TPC = 30` dias (< limiar oficial **45**) |
| Esperado | Impacto negativo monotônico do baixo TPC; **TSA ↓** vs. mesmo mix com TPC 65–75 |

### TC-06 — Sítio D (cobertura de escopo)

| Campo | Valor |
|---|---|
| Objetivo | Homologar comportamento com madeira densa/seca (D) |
| Modo | B |
| Entrada | `pct_D ≥ 0,50` (cenário sintético; n histórico pequeno); demais sítios complementam soma = 1,0; Extrativo_AT ≈ 2,0%; TPC ≈ 55 |
| Esperado | TSA não superior ao baseline A; Carga em faixa aceitável/alta; `dom_D = 1` |

### TC-07 — Mix CDMG elevado

| Campo | Valor |
|---|---|
| Objetivo | Validar `pct_CDMG` e sinergia de madeiras secas/densas |
| Modo | B |
| Entrada | Ex.: `pct_C = 0,40`; `pct_D = 0,20`; `pct_MG = 0,20`; `pct_A = 0,20` → `pct_CDMG = 0,80` |
| Esperado | `pct_CDMG` calculado corretamente; TSA ≤ cenário com `pct_ABC` alto equivalente; sem violação de soma do mix |

### TC-08 — Camada C (entropia, HHI, dominância)

| Campo | Valor |
|---|---|
| Objetivo | Validar engenharia de features obrigatória do PRD |
| Modo | Pipeline / B |
| Entrada A | Mix concentrado: `pct_A = 0,80`; demais = 0,20 distribuídos |
| Entrada B | Mix equilibrado: A=B=C=D=MG = 0,20 |
| Esperado | `dom_A = 1` em A; `mix_hhi` maior em A que em B; `mix_entropy` maior em B; soma pct = 1,0 |

---

## 4. Monotonicidades (Matriz B — estresse físico)

Executar com **demais variáveis fixas** (cenário âncora: mix MIX balanceado, TPC=65, Volume=8.600, Kappa=17).

| ID | Variável | Sequência | Resposta obrigatória |
|---|---|---|---|
| TM-01 | DB_LAB (kg/m³) | 520 → 490 → 460 → 440 | TSA não aumenta (preferencialmente ↓) |
| TM-02 | Extrativo_AT (%) | 1,6 → 2,0 → 2,3 → 2,6 | TSA ↓ |
| TM-03 | TPC (dias) | 75 → 60 → 45 → 30 | TSA ↓ |
| TM-04 | VMI | 0,30 → 0,25 → 0,21 → 0,18 | TSA ↓ |
| TM-05 | Carga (% Na₂O) | 18,5 → 19,5 → 20,5 → 21,3 | TSA ↓ |

---

## 5. Explicabilidade (Matriz C)

### TC-09 — Detrator TPC

| Campo | Valor |
|---|---|
| Cenário | Mesmo de TC-05 (TPC = 30) |
| Esperado | **TPC** aparece no **top-3** detratores; contribuição negativa em ΔTSA |

### TC-10 — Detratores Extrativos / Carga

| Campo | Valor |
|---|---|
| Cenário | Mesmo de TC-03 (Extrativo 2,6%; DB baixa) |
| Esperado | **Extrativo_AT** e/ou **Carga Alcalina** no top-3; se Casca ativa e elevada, pode aparecer |

### Entregável mínimo de explicabilidade

Por cenário homologado: lista ordenada dos 3 atributos com maior impacto estimado e sinal (positivo/negativo) sobre TSA.

---

## 6. Testes de Cascata (Modo A) e Pipeline

### TC-A01 — Integração Elo 1→2→3

| Campo | Valor |
|---|---|
| Objetivo | Validar estimação sem injetar Extrativos/Carga |
| Entrada | Sítio + Idade + Mix + TPC + Volume + DB_SGF + Kappa |
| Esperado | Extrativo_AT estimado na faixa plausível; Carga estimada; TSA gerada; reportar erros por elo se houver ground truth |

### TC-A02 — Proxy DB_LAB

| Campo | Valor |
|---|---|
| Objetivo | Validar imputação |
| Entrada | Apenas DB_SGF (sem Lab) |
| Esperado | Sistema aplica `DB_LAB = 0,985 × DB_SGF` e documenta a origem |

### TC-P01 — Filtro operacional de treino

| Campo | Valor |
|---|---|
| Objetivo | Garantir regra PRD no dataset de treino |
| Esperado | Zero registros com `Produção_Digestor < 1.000` no treino; logar contagem excluída na documentação |

---

## 7. Registro e Validação de Resultados

| ID | Descrição | Variável crítica | Resultado esperado | Status |
|---|---|---|---|---|
| TC-01 | Escala Sítio A | Volume ≥ 10.000; DB 480 | Alta produção / estabilidade | |
| TC-02 | Equilíbrio Sítio B | Carga 19–21% | Alinhado ao baseline | |
| TC-03 | Estresse Sítio C | DB 455; Extr. 2,6% | Queda severa de TSA | |
| TC-04 | Mix diluidor | ↑ pct_ABC | Ganho vs. base seca | |
| TC-05 | TPC verde | TPC = 30 | Penalização de rendimento | |
| TC-06 | Sítio D | pct_D ≥ 0,50 | Comportamento coerente + dom_D | |
| TC-07 | CDMG | pct_CDMG alto | Cálculo e TSA coerentes | |
| TC-08 | Camada C | entropy / HHI / dom | Features corretas | |
| TM-01…05 | Monotonicidades | DB/Extr/TPC/VMI/Carga | Direção física | |
| TC-09 | Explicabilidade TPC | Top-3 | TPC no top-3 | |
| TC-10 | Explicabilidade química | Top-3 | Extr. e/ou Carga no top-3 | |
| TC-A01 | Cascata integração | Modo A | Elos encadeados | |
| TC-A02 | Imputação DB | 0,985×SGF | Proxy aplicado | |
| TC-P01 | Filtro <1.000 | Pipeline | Treino limpo | |
| Matriz A | Holdout | MAE | **≤ 56 TSA/dia** | |

---

## 8. Critérios de Pass / Fail

| Resultado | Regra |
|---|---|
| **Pass** | Direção física correta **e** (quando aplicável) faixa numérica respeitada |
| **Fail** | Violação de monotonicidade, unidade errada, mix ≠ 1,0, ou MAE > 56 na Matriz A |
| **Bloqueio de release** | Qualquer Fail em Matriz A, B ou C |

---

## 9. Rastreabilidade com o PRD

| Requisito PRD | Casos que cobrem |
|---|---|
| Mix A/B/C + D/MG | TC-01…07, TC-08 |
| Cascata Elo 1/2/3 | TC-A01, Modos A/B |
| Consistência física | TM-01…05, TC-03, TC-05 |
| Explicabilidade | TC-09, TC-10 |
| MAE ≤ 56 | Matriz A |
| Fator 0,985 | TC-A02 |
| Filtro <1.000 | TC-P01 |
| Kappa / Volume | TC-01, TC-02, TC-03 |

---

*Casos de Teste v1.1 — reconstruídos com integridade a partir do PDF original, da base QM×Processo e do PRD v1.1. Fecham as lacunas D-01 a D-17 na camada de homologação.*

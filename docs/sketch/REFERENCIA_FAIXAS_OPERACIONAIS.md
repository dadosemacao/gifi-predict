# Referência de Faixas Operacionais — Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Status:** Proposta técnica para validação com stakeholder (Thiago Salles)  
**Fonte de evidência:** `excels/Base de dados QM x Processo 2018-2025_consolidado(Dados).xlsx`  
**Documento relacionado:** `docs/sketch/DIVERGENCIAS_E_MITIGACAO_GIFI.md`

---

## 1. Objetivo

Unificar faixas, unidades e limiares citados no PRD, no Resumo Técnico e nos Casos de Teste, com base na distribuição empírica da base histórica (2018–2025).

Esta referência é a **fonte única proposta** para:

- engenharia de features e validação de schema;
- cenários de homologação (TC-01 a TC-10);
- testes de consistência física (monotonicidade);
- alinhamento documental (fechamento de D-01 a D-14).

---

## 2. Escopo da Base Analisada

| Atributo | Valor observado |
|---|---|
| Período | 2018-04-01 a 2025-10-30 |
| Registros | 7.573 (granularidade por turno) |
| Produção mínima | 3.001 TSA/dia |
| Produção máxima | 3.650 TSA/dia |
| Média TSA | 3.414 TSA/dia |
| Desvio-padrão TSA | 98,4 TSA/dia |
| Filtro PRD (< 1.000 TSA/dia) | **0 registros** nesta base (já filtrada ou sem paradas nessa faixa) |

**Nota:** O MAE-alvo de 56 TSA/dia equivale a ~1,6% da média e ~57% de 1 desvio-padrão — meta ambiciosa, mas numericamente coerente com a escala da produção.

---

## 3. D-02 — Unidade de Densidade Básica (decisão)

### Evidência

| Variável | n | min | p50 | max | % valores > 100 |
|---|---|---|---|---|---|
| Densidade básica Lab | 6.920 | 409 | 483 | 528 | **100%** |
| Densidade básica SGF | 7.564 | 450 | 490 | 528 | **100%** |

Valores típicos de densidade básica de eucalipto em polpação situam-se em **400–550 kg/m³**. Em g/cm³, o equivalente seria **0,40–0,55**.

### Decisão proposta

| Item | Valor unificado |
|---|---|
| **Unidade oficial** | **kg/m³** |
| **Unidade proibida em docs/testes** | g/cm³ (erro de nomenclatura nos Casos de Teste) |
| **Validação de schema** | rejeitar ou alertar se `DB_LAB` ou `DB_SGF` ∉ [350, 650] |
| **Ajuste nos testes** | TC-01/02/03: trocar rótulo `g/cm³` → `kg/m³` mantendo os números (465, 475, 470) |

**Conclusão D-02:** a base usa **kg/m³**. Os Casos de Teste rotularam incorretamente a mesma escala numérica como g/cm³.

---

## 4. Taxonomia de Zonas (padrão único)

Para todas as variáveis abaixo, usar três zonas:

| Zona | Significado operacional |
|---|---|
| **Ótima** | Faixa preferencial de operação / planejamento |
| **Aceitável** | Dentro da experiência histórica, com atenção |
| **Crítica** | Fora do padrão histórico usual; exige alerta e teste de estresse |

Limiares derivados preferencialmente de **percentis empíricos** (p05 / p25–p75 / p95), reconciliados com o PRD quando houver aderência.

---

## 5. Densidade Básica Lab (DB_LAB) — fecha D-01

### Distribuição observada

| Estatística | Valor (kg/m³) |
|---|---|
| p05 | 457 |
| p25 | 471 |
| p50 | 483 |
| p75 | 495 |
| p95 | 510 |
| p99 | 519 |

### Conflito documental

| Fonte | Afirmação | Julgamento vs. dados |
|---|---|---|
| PRD | Ideal 470–510 | **Aderente** (cobre ~p25 a p95) |
| TC-01 | Ótimo 400–500 | **Frouxo** no piso; 400 está abaixo do mínimo observado (409) e fora do p01 |
| TC-03 | Mínimo crítico 490; 470 “abaixo do crítico” | **Incorreto**; 490 ≈ p75 (zona alta), 470 ≈ p25 (início da faixa ótima) |

### Proposta unificada

| Zona | Faixa (kg/m³) | Critério empírico |
|---|---|---|
| **Ótima** | **470 – 510** | Alinha PRD + p25–p95 |
| **Aceitável baixa** | **450 – 470** | p05–p25 |
| **Aceitável alta** | **510 – 520** | p95–p99 |
| **Crítica** | **< 450 ou > 520** | Fora de p05–p99 |

### Valores sugeridos para casos de teste

| Teste | DB_LAB proposto | Justificativa |
|---|---|---|
| TC-01 (Sítio A, escala) | **480 kg/m³** | Próximo da mediana global/Sítio A |
| TC-02 (Sítio B, equilíbrio) | **483 kg/m³** | Mediana do Sítio B dominante |
| TC-03 (estresse DB baixa) | **455 kg/m³** | ≈ p05 (zona aceitável baixa / limiar crítico) — **não** 470 |
| Monotonicidade DB | 520 → 490 → 460 → 440 | Sequência decrescente esperando TSA ↓ (com demais variáveis fixas) |

**Comportamento quadrático em U (PRD):** a correlação linear global DB_LAB × TSA é fraca (ρ ≈ +0,04 no conjunto completo; ρ ≈ −0,17 no subset com Extrativo AT). Manter a hipótese de U no modelo, mas **não** usar “DB < 490 = crítico” como regra de homologação.

---

## 6. Densidade Básica SGF e fator de imputação — fecha D-07 (parcial)

### Distribuição DB_SGF

| Estatística | Valor (kg/m³) |
|---|---|
| p05 | 471 |
| p50 | 490 |
| p95 | 509 |

### Otimização empírica do fator `DB_LAB ≈ k × DB_SGF` (n = 6.915)

Busca em grade `k ∈ [0,80 ; 1,05]` com passo 0,001, minimizando MAE.

| Método | k / modelo | MAE | RMSE | Bias | % \|erro\| ≤ 15 |
|---|---|---|---|---|---|
| **Ótimo MAE/RMSE** | **k = 0,985** | **12,02** | **15,24** | **+0,32** | **67,5%** |
| Mediana da razão | k = 0,985 | 12,02 | 15,24 | +0,32 | 67,5% |
| PRD | k = 0,88 | 51,81 | 53,89 | +51,78 | 0,4% |
| Identidade | k = 1,00 | 13,59 | — | — | — |
| Afim (mín. QM) | `0,6255×SGF + 176,48` | 11,78 | 14,66 | 0,00 | — |

**Validação temporal (holdout por ano):** k treinado fora do ano de teste fica entre **0,982 e 0,987**; MAE médio CV ≈ **12,5** vs **52,1** com k=0,88.

**Bootstrap (200–500 reamostragens):**
- mediana da razão: **0,9847** (IC95% **0,9840–0,9855**)
- k ótimo por MAE: **0,985** (IC95% **0,984–0,985**)

### Valor oficial proposto

| Item | Valor unificado |
|---|---|
| Unidade DB_SGF | **kg/m³** |
| **Fator de imputação MVP** | **`DB_LAB = 0,985 × DB_SGF`** |
| Alternativa (se quiser mínimo erro absoluto) | modelo afim `0,6255×SGF + 176,48` (MAE 11,8; menos interpretável) |
| Fator PRD 0,88 | **Rejeitado pela evidência** (viesado +52 kg/m³) |
| Elo 2 (cascata) | Usar DB_SGF quando disponível; converter para proxy Lab só no Elo 3 se o modelo foi treinado em Lab |

**Ação:** atualizar PRD seção 3.1 com **k = 0,985** (não depende de workshop para a escolha numérica; stakeholder só confirma se há razão de processo para manter 0,88).

---

## 7. Extrativos Álcool-Toluol — fecha D-03

### Distribuição observada (n = 2.527; cobertura forte a partir de 2024)

| Estatística | Valor (%) |
|---|---|
| p05 | 1,31 |
| p10 | 1,44 |
| p25 | 1,66 |
| p50 | 1,89 |
| p75 | 2,12 |
| p95 | 2,58 |
| p99 | 2,96 |

### Relação com TSA (evidência de detrator)

| Faixa Extrativo AT | n | TSA médio |
|---|---|---|
| ≤ 1,5% | 348 | 3.416 |
| 1,5–1,8% | 645 | 3.416 |
| 1,8–2,0% | 609 | 3.403 |
| 2,0–2,2% | 458 | 3.405 |
| 2,2–2,5% | 304 | 3.385 |
| 2,5–3,0% | 147 | 3.354 |
| > 3,0% | 16 | 3.361 |

ρ(Extrativo AT, TSA) ≈ **−0,13** (subset completo) a **−0,13** (subset com demais variáveis).

### Conflito documental

| Fonte | Afirmação | Julgamento |
|---|---|---|
| PRD | Esperado 1,5%–3,0% | **Aderente** (≈ p10–p99) |
| TC-01 | Teto 2,0% | **Parcial** — próximo do teto ótimo empírico (2,1%) |
| TC-03 | Teto crítico 1,5%; 2,5% “acima do crítico” | **Invertido** — 1,5% é piso típico, não teto |

### Otimização empírica do limiar (n = 2.527)

Para cada candidato `t`, comparou-se TSA médio com Extrativo ≤ t vs > t.

| Critério | Melhor t | % acima de t | ΔTSA (abaixo − acima) | Cohen’s d | t-stat |
|---|---|---|---|---|---|
| **Máximo t-stat / R² binário** | **2,10%** | 26,6% | **+37,7** | 0,32 | **6,69** |
| **Máximo efeito / Cohen’s d** | **2,45%** | 7,8% | **+54,3** | **0,46** | 5,21 |
| Mesmo ótimo em residual (controlando Carga, TPC, DB) | **2,45%** | 7,8% | +31,8 residual | 0,28 | — |
| Queda visível nos bins de 0,1% | a partir de **2,1%** | — | bin 2,1–2,2: TSA 3.378 | — | — |

Interpretação:
- **2,10%** = melhor ponto de corte operacional (maior significância; ~1/4 da amostra acima).
- **2,45%** = melhor limiar de **zona crítica** (maior queda de TSA; ~8% dos casos).
- Controlando Carga/TPC/DB, o efeito residual ainda aponta **2,45%** → não é só confusão com carga.

### Proposta unificada (valores ótimos pelos dados)

| Zona | Faixa (%) | Critério empírico |
|---|---|---|
| **Ótima** | **1,5 – 2,1** | Abaixo do melhor corte por t-stat/R² |
| **Aceitável** | **2,1 – 2,45** | Acima do teto ótimo; ainda não no pico de efeito |
| **Crítica** | **> 2,45** | Máximo ΔTSA e Cohen’s d; confirmado em residual |
| **Extrema** | **> 3,0** | Raro (p99 ≈ 2,96); estresse máximo |

**Arredondamento de negócio (se preferir décimos “limpos”):** ótima até **2,1%**; crítica a partir de **2,5%** (quase idêntico a 2,45; p95 ≈ 2,58).

### Valores sugeridos para testes

| Teste | Extrativo AT | Justificativa |
|---|---|---|
| TC-01 | **1,8%** | Dentro da ótima (manter) |
| TC-03 | **2,6%** | Acima do limiar crítico 2,45% |
| TC-04 base (Sítio C seco) | **2,2%** | Zona aceitável (entre 2,1 e 2,45) |
| Monotonicidade | 1,6 → 2,0 → 2,3 → 2,6 | Extrativos ↑ → TSA ↓ |

**Atenção:** `Extrativo SGF` (média ≈ 4,0) **não** é a mesma escala que `Extrativo álcool toluol` (média ≈ 1,9). O Elo 1 e os testes devem usar **Álcool-Toluol** como variável de processo/laboratório do PRD.

---

## 8. TPC (Tempo Pós-Corte) — fecha D-14

### Distribuição observada

| Estatística | Valor (dias) |
|---|---|
| p01 | 30 |
| p05 | 38 |
| p10 | 43 |
| p25 | 51 |
| p50 | 65 |
| p75 | 85 |
| p95 | 112 |

### Relação com TSA

| Faixa TPC | n | TSA médio | Carga média |
|---|---|---|---|
| ≤ 30 | 72 | 3.342 | 19,99 |
| 30–45 | 994 | 3.378 | 19,88 |
| 45–60 | 2.144 | 3.397 | 19,70 |
| 60–75 | 1.578 | 3.428 | 19,23 |
| 75–90 | 1.272 | 3.439 | 19,43 |
| > 90 | 1.504 | ~3.430 | ~19,5 |

ρ(TPC, TSA) ≈ **+0,18** a **+0,25** (subset).

### Proposta unificada

| Zona | Faixa (dias) | Critério |
|---|---|---|
| **Crítica (madeira verde)** | **< 45** | Abaixo de p10; TSA e carga piores |
| **Aceitável** | **45 – 60** | Recuperação parcial |
| **Ótima / estável** | **60 – 90** | Maior TSA médio |
| **Alta (pátio longo)** | **> 90** | Frequente; sem penalização clara de TSA |

| Item | Valor |
|---|---|
| Limiar oficial “madeira verde” | **45 dias** (confirma TC-05; formalizar no PRD) |
| TC-05 | TPC = **30 dias** (manter; ≈ p01, estresse real) |
| TC-01 (estável) | TPC = **75 dias** (manter; zona ótima) |
| TC-02 | TPC = **65 dias** (manter; mediana) |

---

## 9. Carga Alcalina — fecha parte de D-04 / TC-02 / TC-03

### Distribuição observada

| Estatística | Valor (% Na₂O) |
|---|---|
| p05 | 17,86 |
| p25 | 19,09 |
| p50 | 19,66 |
| p75 | 20,15 |
| p95 | 20,80 |
| p99 | 21,19 |
| max | 21,95 |

### Relação com TSA (principal detrator empírico)

| Faixa Carga | n | TSA médio |
|---|---|---|
| 15–18 | 486 | 3.461 |
| 18–19 | 1.206 | 3.443 |
| 19–20 | 3.452 | 3.413 |
| 20–21 | 2.238 | 3.394 |
| 21–22 | 191 | 3.365 |

ρ(Carga, TSA) ≈ **−0,23** (global) a **−0,37** (subset com Extrativo AT).  
Correlações citadas no TC-03 (ρ = −0,4672) são **mais fortes** que o observado nesta base; usar os valores da base como referência oficial até reestimar no pipeline.

### Proposta unificada

| Zona | Faixa (% Na₂O) | Critério |
|---|---|---|
| **Ótima** | **18,5 – 20,5** | Núcleo operacional (p10–p90 aprox.) |
| **Aceitável** | **17,5 – 21,0** | p05–p99 |
| **Crítica alta** | **> 21,0** | Raro; TSA médio mais baixo |
| **Crítica baixa** | **< 17,5** | Fora do p05 |

### Valores para testes

| Teste | Esperado | Ajuste proposto |
|---|---|---|
| TC-02 (Elo 2) | 19–21% | **Manter** (cobre p25–p95) |
| TC-03 (estresse) | “além de 22%” | Ajustar para **> 21,0%** (ex.: 21,3%); 22% é acima do máximo histórico (21,95) |
| TC-01 | Carga baixa/otimizada | Esperar **≤ 19,5%** em cenário A puro |

---

## 10. Número Kappa — fecha D-08

### Distribuição observada

| Estatística | Valor |
|---|---|
| p05 | 14,96 |
| p25 | 15,73 |
| p50 | 16,28 |
| p75 | 16,98 |
| p95 | 17,91 |
| p99 | 18,51 |

### Proposta unificada

| Zona | Faixa | Critério |
|---|---|---|
| **Meta operacional** | **16 – 18** | Confirma TC-02; cobre o núcleo p40–p95 |
| **Aceitável** | **15 – 18,5** | p05–p99 |
| **Crítica** | **< 15 ou > 18,5** | Extremos |

| Item | Decisão |
|---|---|
| Incluir no PRD? | **Sim** — variável de processo presente na base e nos testes |
| Papel no MVP | Feature de processo **fixa/estimada** no Elo 3 (não gerada pela cascata florestal) |
| TC-02 | Kappa = **17,0** (manter) |
| TC-03 | Kappa = **18,0** (manter; limiar alto da meta, não necessariamente “sub-cozimento extremo”) |

---

## 11. % Casca — fecha D-05 (evidência para decisão de escopo)

### Distribuição observada (n = 4.872; ~64% de cobertura)

| Estatística | Valor (%) |
|---|---|
| p05 | 0,37 |
| p50 | 0,80 |
| p75 | 1,04 |
| p95 | 1,45 |
| p99 | 1,78 |

### Relação com TSA

| Faixa Casca | n | TSA médio |
|---|---|---|
| ≤ 0,5% | 756 | 3.431 |
| 0,5–0,8% | 1.636 | 3.428 |
| 0,8–1,0% | 1.123 | 3.417 |
| 1,0–1,3% | 880 | 3.395 |
| 1,3–1,5% | 297 | 3.382 |
| > 1,5% | 180 | ~3.376 |

ρ(Casca, TSA) ≈ **−0,15**.

### Proposta unificada

| Zona | Faixa (%) |
|---|---|
| **Ótima** | **≤ 1,0** |
| **Aceitável** | **1,0 – 1,5** |
| **Crítica** | **> 1,5** |

| Item | Recomendação |
|---|---|
| Incluir na cascata MVP? | **Sim, se Elo auxiliar for viável** — variável existe, tem sinal e está no Resumo Técnico |
| Se fora do MVP | Remover casca da explicabilidade **obrigatória** do Resumo; manter como feature opcional do Elo 3 quando disponível |
| Premissa de erro em cascata | Documentar MAE do Elo Casca separadamente (mesmo protocolo de Extrativos) |

---

## 12. VMI (Volume Individual Médio)

### Distribuição e bins já existentes na base

| Faixa (m³/árvore) | n | TSA médio |
|---|---|---|
| ≤ 0,21 | 885 | 3.376 |
| 0,21–0,25 | 3.191 | 3.409 |
| 0,25–0,30 | 2.827 | 3.427 |
| > 0,30 | 661 | 3.435 |

ρ(VMI, TSA) ≈ **+0,18**.

### Proposta unificada

| Zona | Faixa |
|---|---|
| **Crítica baixa** | **≤ 0,21** |
| **Aceitável** | **0,21 – 0,25** |
| **Ótima** | **> 0,25** |

Alinha às colunas já presentes na base (`VMI <=0,21`, `VMI 0,21a0,25`, `VMI >0,25`) e ao estresse físico do PRD/Resumo (VMI ↓ → TSA ↓).

---

## 13. Volume abastecido — fecha D-16

### Evidência

| Estatística | Valor (m³) |
|---|---|
| p01 | 4.007 |
| p05 | 5.983 |
| p50 | 8.669 |
| p95 | 10.764 |
| % registros > 1.200 | **99,6%** |

### Conflito com Casos de Teste

TC-01 usa `Volume_m3 > 1.200` e TC-02 usa `1.050`. Na base de referência, esses limiares **não discriminam** operação normal.

### Proposta unificada

| Item | Valor |
|---|---|
| Unidade | m³ (volume abastecido diário associado ao turno) |
| Faixa típica | **6.000 – 11.000 m³** |
| Baixo (atenção) | **< 6.000** (≈ p05) |
| Alto | **> 10.500** (≈ p95) |
| TC-01 (escala alta) | Volume ≥ **10.000 m³** |
| TC-02 (equilíbrio) | Volume ≈ **8.500 – 8.700 m³** (mediana) |

---

## 14. Mix por sítio e dominância — fecha D-09 / D-10 (parcial)

### Frequência de dominância (> 50%)

| Sítio | % dias com pct > 0,50 | pct médio | pct máximo |
|---|---|---|---|
| A | 40,1% | 0,43 | 1,00 |
| B | 7,3% | 0,19 | 0,86 |
| C | 6,4% | 0,15 | 0,88 |
| D | 0,5% | 0,04 | 0,69 |
| MG | ~0% | 0,19 | 0,52 |

Soma média `pct_A+…+pct_MG` ≈ **0,999** (regra de fechamento em 1,0 validada).

### TSA médio por sítio dominante

| Dominância | n | TSA médio | Extrativo AT mediano | Carga mediana |
|---|---|---|---|---|
| A | 3.036 | 3.432 | 1,79 | 19,38 |
| B | 550 | 3.397 | 1,86 | 19,66 |
| C | 483 | 3.387 | 2,00 | 19,81 |
| D | 36 | 3.341 | 1,92 | 19,53 |
| MIX | 3.465 | 3.406 | 1,96 | 19,91 |

### Proposta para testes

| Regra | Valor |
|---|---|
| Flag `dom_X` | **1 se pct_X > 0,50** (manter PRD) |
| TC puro A/B/C | Preferir `pct ≥ 0,95` quando possível; **B e C 100% são raros/inexistentes** na base (B≥0,95 e C≥0,95 = 0 linhas) |
| TC-01 | `pct_A = 1,0` aceitável como cenário sintético; ancorar expectativas em A dominante real |
| TC-06 (novo) | Sítio D com `pct_D ≥ 0,50` (n histórico pequeno — cenário sintético) |
| TC-07 (novo) | `pct_CDMG` elevado (ex.: C=0,4 + D=0,2 + MG=0,2) |

---

## 15. Produção TSA e critério MAE — fecha D-13 / D-17

| Item | Valor unificado |
|---|---|
| Alvo | Produção digestor (TSA/dia) |
| Escala típica | **3.200 – 3.550** (p05–p95) |
| Filtro de treino PRD | Excluir `< 1.000 TSA/dia` (manter regra; nesta base não há efeito prático) |
| **MAE de aceite** | **`MAE_holdout ≤ 56 TSA/dia`** (substituir “próximo a”) |
| Baseline ingênuo | Desvio-padrão ≈ 98 TSA/dia → MAE 56 é ~43% melhor que erro típico de 1σ se o modelo for centrado |

---

## 16. Tabela-mestra consolidada (valores oficiais propostos)

| Variável | Unidade | Ótima | Aceitável | Crítica | Valor âncora (mediana) |
|---|---|---|---|---|---|
| DB_LAB | kg/m³ | 470–510 | 450–470 / 510–520 | <450 ou >520 | 483 |
| DB_SGF | kg/m³ | 475–505 | 465–475 / 505–515 | <465 ou >515 | 490 |
| Extrativo AT | % | 1,5–2,1 | 2,1–2,45 | >2,45 | 1,89 |
| TPC | dias | 60–90 | 45–60 | <45 | 65 |
| Carga Alcalina | % Na₂O | 18,5–20,5 | 17,5–21,0 | >21,0 ou <17,5 | 19,66 |
| Kappa | — | 16–18 | 15–18,5 | <15 ou >18,5 | 16,28 |
| % Casca | % | ≤1,0 | 1,0–1,5 | >1,5 | 0,80 |
| VMI | m³ | >0,25 | 0,21–0,25 | ≤0,21 | 0,25 |
| Volume | m³ | 7.500–9.500 | 6.000–7.500 / 9.500–10.500 | <6.000 | 8.669 |
| Mix soma | fração | = 1,00 | 0,98–1,02 | fora | ≈1,00 |
| TSA | TSA/dia | 3.350–3.500 | 3.200–3.350 / 3.500–3.600 | <3.200* | 3.450 |

\*Em operação contínua desta base; paradas profundas (<1.000) ficam fora do treino por regra de negócio.

---

## 17. Correlações de referência (sinais físicos esperados)

Subset com Extrativo AT + demais variáveis (n ≈ 2.004):

| Par | ρ observado | Direção esperada na homologação |
|---|---|---|
| Carga → TSA | **−0,37** | Carga ↑ → TSA ↓ |
| TPC → TSA | **+0,25** | TPC ↓ (verde) → TSA ↓ |
| Extrativo AT → TSA | **−0,13** | Extrativos ↑ → TSA ↓ |
| Casca → TSA | **−0,15** | Casca ↑ → TSA ↓ |
| VMI → TSA | **+0,09 a +0,18** | VMI ↓ → TSA ↓ |
| Extrativo AT → Carga | **+0,26** | Extrativos ↑ → Carga ↑ (Elo 2) |
| TPC → Carga | **−0,40** | TPC ↓ → Carga ↑ |

Usar estes sinais como **critério de consistência física** (Matriz B), independentemente do MAE.

---

## 18. Impacto direto nas divergências

| ID | Decisão desta referência |
|---|---|
| **D-02** | Unidade = **kg/m³** (confirmado pela base) |
| **D-01** | Ótimo DB = **470–510**; crítico ≠ 490; TC-03 deve usar ~**455** |
| **D-03** | Ótimo Extrativos = **1,5–2,1**; crítico = **>2,45** (otimizado por ΔTSA/Cohen; 1,5 não é teto) |
| **D-07** | Imputação **0,985 × DB_SGF** (ótimo MAE; IC95% 0,984–0,985; rejeita 0,88) |
| **D-08** | Kappa **16–18** entra no PRD como processo |
| **D-14** | Limiar madeira verde = **45 dias** |
| **D-13** | Aceite = **MAE ≤ 56** |
| **D-16** | Volume de teste na escala **6.000–11.000 m³** |
| **D-05** | Casca tem sinal; decidir inclusão na cascata com faixas desta tabela |
| **D-17** | Filtro <1.000: manter regra; impacto nulo nesta base |

---

## 19. Próximos passos

1. Apresentar ao stakeholder os valores já otimizados pelos dados: fator **0,985** e Extrativos **ótimo ≤2,1% / crítico >2,45%** (arredondável a 2,5%). Confirmar apenas se há restrição de processo que force manter 0,88.
2. Atualizar PRD v1.1 e Casos de Teste v1.1 com os valores da seção 16.
3. Implementar validação de schema no pipeline com as faixas críticas.
4. Reestimar correlações no dataset de treino final (pós-agregação diária) e substituir os ρ citados no TC-03.

---

## 20. Rastreabilidade

| Artefato | Uso |
|---|---|
| Base Excel QM × Processo 2018–2025 | Fonte empírica única desta proposta |
| PRD / Resumo / Casos de Teste | Fontes documentais reconciliadas |
| `DIVERGENCIAS_E_MITIGACAO_GIFI.md` | Catálogo de conflitos que esta referência resolve |

---

*Proposta técnica. Não substitui a validação formal do stakeholder; após aprovação, promover para anexo oficial do PRD.*

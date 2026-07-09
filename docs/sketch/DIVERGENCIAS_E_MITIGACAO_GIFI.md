# Análise de Divergências Documentais — Projeto GIFI

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Papel:** Cientista de Dados Sênior — Análise Preditiva  
**Documentos analisados (origem):**
- `docs/Documento de Requisitos do Produto (PRD) - Projeto GIFI.pdf`
- `docs/Resumo Técnico_ Projeto GIFI.pdf`
- `docs/Seção de Casos de Testes Funcionais e Homologação.pdf`

**Resolução documental (v1.1 — 2026-07-09):** as divergências D-01 a D-17 foram incorporadas e fechadas nos artefatos reconstruídos:
- `docs/PRD_GIFI_v1.1.md`
- `docs/RESUMO_TECNICO_GIFI_v1.1.md`
- `docs/CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md`
- `docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md`

Este arquivo permanece como **histórico de análise** e rastreabilidade das decisões.

---

## 1. Síntese do Problema de Negócio

O Projeto GIFI busca resolver uma limitação estrutural do planejamento florestal e industrial da Veracel: **prever produção diária de celulose (TSA/dia) em cenários de longo prazo (2025/2026) sem depender de variáveis históricas imediatas (lags)**.

### Framing analítico correto (visão sênior)

| Dimensão | Definição consolidada |
|---|---|
| **Variável-alvo** | Produção diária de TSA (agregada por turno → meta diária) |
| **Horizonte** | Simulação de cenários futuros de abastecimento florestal |
| **Entrada** | Mix de madeira por sítio (A, B, C, D, MG), qualidade ponderada por volume, parâmetros de processo fixos ou estimados |
| **Restrição metodológica** | Exclusão total de lags para viabilizar simulação em talhões ainda não cortados |
| **Decisão operacional** | Ajustar frentes de colheita e mix de abastecimento com base na produção estimada |
| **Uso secundário** | Isolar desvios entre planejado, estimado e realizado (madeira vs. fábrica) |

A solução proposta é um **simulador preditivo em cascata** ("Caminho da Ida") com interface web para upload de cenários, validado por MAE ≤ 56 TSA/dia, consistência física e explicabilidade de detratores.

---

## 2. Mapa de Alinhamento entre Documentos

| Tema | PRD | Resumo Técnico | Casos de Teste | Status |
|---|---|---|---|---|
| Exclusão de lags | Sim | Sim | Implícito | Alinhado |
| Caminho da Ida (cascata) | Sim (3 elos) | Sim (4 variáveis na premissa) | Sim (Elo 1/2/3) | Parcial |
| MAE ~ 56 TSA/dia (holdout 2026) | Sim | Sim | Sim (critério geral) | Parcial |
| Consistência física (estresse) | DB e VMI | DB, VMI e Extrativos | DB, Extrativos, TPC, Mix | Parcial |
| Explicabilidade | TPC e Carga Alcalina | TPC, Casca e Carga Alcalina | Comportamento, sem teste de saída | Parcial |
| Interface web até 31/08 | Marco 2 | KPI explícito | Ambiente de homologação | Alinhado |
| Sítios A–MG | 5 sítios no mix | 5 sítios citados | Apenas A, B, C testados | Divergente |
| Algoritmos (ElasticNet/RF/NN) | Sim | Não especifica | Não especifica | Lacuna |
| Faixas de DB e Extrativos | Definidas | Não detalhadas | Faixas conflitantes | Divergente |

---

## 3. Divergências Identificadas

As divergências foram classificadas por **severidade** segundo impacto em modelagem, validação e homologação.

- **Crítica:** pode invalidar modelo, testes ou aceite do produto
- **Alta:** gera ambiguidade operacional ou risco de falso positivo/negativo na homologação
- **Média:** lacuna de cobertura ou inconsistência documental sem bloqueio imediato
- **Baixa:** diferença de granularidade ou nomenclatura

---

### D-01 — Faixas de Densidade Básica (DB_LAB) conflitantes

| Fonte | Definição |
|---|---|
| **PRD** | Faixa ideal global: **470–510 kg/m³**; comportamento quadrático em U |
| **TC-01** | Faixa ótima: **400–500 kg/m³**; DB_LAB = 465 |
| **TC-03** | Mínimo crítico: **490 kg/m³**; DB_LAB = 470 classificado como "abaixo do crítico" |

**Problema:** O valor 470 kg/m³ é simultaneamente o **início da faixa ideal do PRD** e **abaixo do mínimo crítico dos testes**. As faixas 400–500 e 470–510 não são reconciliáveis sem decisão explícita.

**Impacto:** Testes de estresse físico (TC-03) podem reprovar cenários que o PRD considera válidos, ou aprovar cenários fora da física operacional.

**Mitigação:**
1. Publicar uma **tabela única de referência** (`docs/sketch/REFERENCIA_FAIXAS_OPERACIONAIS.md` ou seção no PRD) com faixas por sítio e contexto (ótimo, aceitável, crítico).
2. Validar faixas com o stakeholder (Thiago Salles) e engenharia de processo antes da homologação.
3. Ajustar TC-01 e TC-03 para usar a mesma escala (**kg/m³**) e os mesmos limiares.
4. Incluir teste de monotonicidade: DB ↓ → TSA ↓, com valores ancorados na tabela aprovada.

---

### D-02 — Unidades de medida inconsistentes (kg/m³ vs. g/cm³)

| Fonte | Unidade usada |
|---|---|
| **PRD** | kg/m³ |
| **Casos de Teste** | g/cm³ (ex.: DB_LAB = 465 g/cm³) |

**Problema:** Densidade básica de madeira em polpação é tipicamente expressa em **kg/m³** (465 kg/m³ ≈ 0,465 g/cm³). O uso de g/cm³ nos testes sugere erro de unidade de **ordem de magnitude**.

**Impacto:** Cenários de teste podem ser interpretados incorretamente na interface e no pipeline de features.

**Mitigação:**
1. Padronizar **kg/m³** em PRD, planilhas de cenário, interface e casos de teste.
2. Adicionar validação de schema na ingestão: `400 ≤ DB_LAB ≤ 600` (kg/m³) com alerta fora da faixa.
3. Revisar TC-01, TC-02 e TC-03 com valores corrigidos.

---

### D-03 — Faixas de Extrativos contraditórias

| Fonte | Definição |
|---|---|
| **PRD** | Faixa esperada: **1,5%–3,0%**; principal detrator químico |
| **TC-01** | Extrativos 1,8% descritos como "abaixo do teto de **2,0%**" |
| **TC-03** | Extrativos 2,5% descritos como "acima do teto crítico de **1,5%**" |
| **Resumo Técnico** | Aumento de extrativos deve reduzir TSA (estresse físico) |

**Problema:** O PRD trata 1,5% como **piso** da faixa esperada; os testes tratam 1,5% como **teto crítico**. O teto de 2,0% no TC-01 não existe no PRD.

**Impacto:** O Elo 1 (estimação de extrativos) e os testes de penalização química ficam sem critério unificado.

**Mitigação:**
1. Definir três zonas operacionais: **ótima** (ex.: 1,5%–2,0%), **aceitável** (2,0%–3,0%), **crítica** (> 3,0% ou limiar validado por processo).
2. Alinhar PRD, Resumo Técnico e casos de teste à mesma taxonomia.
3. Adicionar TC-06: monotonicidade `Extrativos ↑ → TSA ↓`, ausente no PRD mas exigido no Resumo Técnico.

---

### D-04 — Consistência física: variáveis de estresse incompletas no PRD

| Fonte | Variáveis de estresse |
|---|---|
| **PRD** | Queda de DB e redução severa de VMI → declínio de TSA |
| **Resumo Técnico** | Queda de DB, redução de VMI **e aumento de Extrativos** → queda proporcional de TSA |
| **Casos de Teste** | DB, Extrativos, TPC, Mix (comportamento direcional) |

**Problema:** O PRD omite extrativos e TPC nos critérios de consistência física, enquanto os outros documentos os tratam como obrigatórios.

**Impacto:** Um modelo pode ser aceito pelo PRD literal, mas reprovado na homologação funcional.

**Mitigação:**
1. Atualizar o PRD (seção 4.2) para incluir: `Extrativos ↑ → TSA ↓`, `TPC abaixo do limiar → TSA ↓`, `Mix diluidor → TSA ↑` em relação ao cenário base.
2. Formalizar **testes de monotonicidade** como critério de aceite independente do MAE.
3. Documentar no relatório de modelagem a verificação de sinais de correlação (ex.: ρ = −0,4672 para Carga Alcalina citado no TC-03).

---

### D-05 — Cascata de estimação: % Casca ausente no PRD

| Fonte | Cadeia de estimação |
|---|---|
| **PRD Elo 1** | Sítio + Idade → **Extrativos** |
| **PRD Elo 2** | Extrativos + TPC + DB_SGF → **Carga Alcalina** |
| **Resumo Técnico (premissa)** | Sítio + Idade → Extrativos **e % Casca** → Carga → TSA |
| **Resumo (explicabilidade)** | Perdas por **alta concentração de casca** |

**Problema:** O Resumo Técnico assume estimação de % Casca na cascata e na explicabilidade; o PRD não define elo, variável de entrada ou decomposição para casca.

**Impacto:** Lacuna na engenharia de features e na capacidade de explicar desvios atribuídos à casca.

**Mitigação:**
1. Decisão de escopo com stakeholder:
   - **Opção A (MVP):** % Casca fora da cascata; removida da explicabilidade obrigatória no Resumo.
   - **Opção B (recomendada se dado existir):** Incluir Elo 1b ou expandir Elo 1: `Sítio + Idade → % Casca`, com modelo auxiliar e propagação de erro documentada.
2. Registrar a decisão em `docs/sketch/DECISAO_CASCATA_CASCA.md`.
3. Ajustar premissa em aberto do Resumo Técnico conforme a opção escolhida.

---

### D-06 — Entrada da cascata vs. injeção direta nos testes

| Fonte | Fluxo de entrada |
|---|---|
| **PRD** | Elo 1 estima Extrativos a partir de Sítio + Idade; usuário não fornece extrativos em cenários futuros |
| **TC-01, TC-03** | `Extrativos_Pct` fornecido diretamente no cenário de entrada |

**Problema:** Os testes isolam efeitos injetando extrativos, mas não validam o **Elo 1** (estimação por Sítio + Idade). A homologação pode validar o modelo final sem validar a cadeia completa.

**Impacto:** Erro acumulado na cascata (premissa em aberto do Resumo) pode explodir sem detecção.

**Mitigação:**
1. Separar dois modos de teste:
   - **Modo A — Integração completa:** apenas Sítio, Idade, TPC, mix e volume; extrativos e carga estimados.
   - **Modo B — Isolamento de elos:** injeção controlada para validar Elo 2 e Elo 3.
2. Definir métricas por elo: MAE_Extrativos, MAE_Carga, MAE_TSA.
3. Estabelecer teto de erro composto: `MAE_TSA ≤ 56` com decomposição de contribuição por elo no relatório de aderência.

---

### D-07 — DB_SGF no Elo 2 vs. DB_LAB nos testes e no mix

| Fonte | Densidade utilizada |
|---|---|
| **PRD Elo 2** | Densidade **SGF** |
| **PRD imputação** | DB_Lab = DB_SGF × 0,88 quando laboratorial ausente |
| **PRD qualidade** | DB_LAB ponderada por volume no modelo final |
| **Casos de Teste** | DB_LAB injetada diretamente |

**Problema:** Não está claro se o Elo 3 consome DB_LAB, DB_SGF ou ambas; os testes usam DB_LAB enquanto o Elo 2 referencia SGF.

**Impacto:** Risco de inconsistência entre treino, inferência e cenários simulados.

**Mitigação:**
1. Diagrama de dados único: em cada elo, qual variável de densidade entra e como se converte.
2. Regra explícita: em simulação futura sem laboratório, usar DB_SGF × 0,88 como proxy de DB_LAB.
3. Testes devem declarar se DB_LAB é medida ou derivada de DB_SGF.

---

### D-08 — Variável Kappa presente nos testes, ausente no PRD

| Fonte | Número Kappa |
|---|---|
| **TC-02** | Kappa = 17,0 (meta 16–18) |
| **TC-03** | Kappa = 18,0 (sub-cozimento) |
| **PRD / Resumo** | Não mencionado em features, cascata ou explicabilidade |

**Problema:** Testes condicionam comportamento esperado a uma variável de processo não especificada no desenho do modelo.

**Impacto:** Falha em TC-02/TC-03 pode ocorrer por omissão de feature, não por defeito do algoritmo.

**Mitigação:**
1. Incluir Kappa como **variável de processo fixa** no PRD (seção 3.3 ou 4.1), com faixa operacional 16–18.
2. Se Kappa for apenas parâmetro de validação e não feature do modelo, remover dos testes ou marcar como **pré-condição de cenário**, não como saída esperada do Elo 2.
3. Documentar se Kappa entra no Elo 3 ou apenas restringe cenários de homologação.

---

### D-09 — Cobertura de sítios: cinco no escopo, três nos testes

| Fonte | Sítios |
|---|---|
| **PRD** | A, B, C, D, MG (pct_D, pct_MG, pct_CDMG, dom_X) |
| **Resumo** | A, B, C, D, MG citados; premissa de qualidade foca A, B, C |
| **Casos de Teste** | Apenas A, B, C |

**Problema:** Sítios D e MG, variáveis `pct_CDMG`, `pct_D`, `pct_MG` e flags `dom_D`, `dom_MG` não possuem casos de teste.

**Impacto:** Comportamento do mix com madeira seca/densa (CDMG) e dominância de D/MG não homologado.

**Mitigação:**
1. Adicionar TC-06 (Sítio D ou MG isolado) e TC-07 (mix com pct_CDMG elevado).
2. Incluir teste de dominância: `dom_X = 1` quando pct_X > 0,50.
3. Priorizar cenários reais de planejamento 2025/2026 que usem D e MG.

---

### D-10 — Camada C do mix (entropia, HHI, dominância) sem validação

| Fonte | Índices de diversidade |
|---|---|
| **PRD** | mix_entropy, mix_hhi, dom_X obrigatórios |
| **Casos de Teste** | TC-04 menciona pct_ABC; não testa entropia, HHI ou flags |

**Problema:** Features obrigatórias de engenharia sem critério de homologação.

**Impacto:** Regressão silenciosa se índices forem calculados incorretamente.

**Mitigação:**
1. Testes unitários de engenharia de features (Camadas A, B, C) separados do modelo ML.
2. TC-08: cenário com troca abrupta de mix → verificar aumento de entropia e resposta estável do TSA.
3. Checklist de pipeline: soma de pct_* = 1,0; dom_X dispara em > 50%.

---

### D-11 — Explicabilidade: escopo diferente entre documentos

| Fonte | Detratores explicáveis |
|---|---|
| **PRD** | Madeira jovem (TPC), variações na Carga Alcalina |
| **Resumo Técnico** | TPC, **casca**, sobredosagem de Carga Alcalina; decomposição de impacto |
| **Casos de Teste** | Nenhum TC valida saída explicativa (SHAP, importância, decomposição) |

**Problema:** Critério de aceite exige explicabilidade, mas não há teste funcional que valide o artefato de explicação.

**Impacto:** Homologação subjetiva; risco de entregar gráfico de importância genérico sem vínculo com a decisão de negócio.

**Mitigação:**
1. Definir entregável mínimo: relatório por cenário com top-3 detratores e contribuição em TSA (ou ΔTSA).
2. TC-09: cenário TC-05 (TPC baixo) deve ranquear TPC entre os principais detratores.
3. TC-10: cenário TC-03 deve ranquear Extrativos e/ou Carga Alcalina como detratores.
4. Alinhar lista de detratores obrigatórios entre PRD e Resumo após decisão sobre casca (D-05).

---

### D-12 — Gestão de desvios vs. análise automática de causa raiz

| Fonte | Gestão de desvios |
|---|---|
| **PRD (objetivo)** | Ferramenta para isolar e explicar desvios planejado/estimado/realizado |
| **Resumo (fora do escopo)** | Análise automática de causa raiz via IA genética |

**Problema:** O objetivo de negócio inclui gestão de desvios, mas o Resumo exclui automação de causa raiz sem definir o que permanece no MVP (ex.: relatório manual assistido por importância de atributos).

**Impacto:** Expectativa do stakeholder pode incluir diagnóstico automatizado não previsto no cronograma.

**Mitigação:**
1. Esclarecer no PRD: MVP entrega **explicabilidade assistida** (importância/decomposição), não RCA autônoma.
2. Fluxo MVP: usuário informa período com desvio → sistema retorna contribuição dos atributos → analista interpreta.
3. Registrar "Caminho da Volta" e "RCA automática" como fase 2 explícita.

---

### D-13 — Critério MAE: definição operacional insuficiente

| Fonte | MAE |
|---|---|
| **PRD / Resumo / Testes** | "Próximo ao teto de 56 TSA/dia" em holdout 2026 |
| **Lacuna** | Não define se aceite é MAE ≤ 56, < 56, ou 56 ± tolerância |

**Problema:** "Próximo" é subjetivo; testes funcionais misturam critério estatístico (MAE) com critério comportamental (direção física) sem separação.

**Impacto:** Disputa na homologação final.

**Mitigação:**
1. Definir contrato numérico: ex. `MAE_holdout_2026 ≤ 56 TSA/dia` e, opcionalmente, `WAPE ≤ X%`.
2. Separar matrizes de aceite:
   - **Matriz A — Estatística:** holdout temporal 2026.
   - **Matriz B — Comportamental:** TC-01 a TC-10 (monotonicidade e cenários).
3. Exigir ambas para aceite, não intercambiáveis.

---

### D-14 — Limiar de TPC "madeira verde" não definido no PRD

| Fonte | TPC |
|---|---|
| **TC-05** | TPC = 30 dias; limite implícito = **45 dias** |
| **PRD / Resumo** | "Madeira jovem / baixo TPC" sem limiar numérico |

**Problema:** O teste usa 45 dias como referência; o PRD não formaliza esse limiar operacional.

**Impacto:** Penalização de TPC pode ser inconsistente entre modelo e regra de negócio.

**Mitigação:**
1. Validar com operações o limiar de madeira verde (30, 45 ou por sítio).
2. Incluir no PRD como regra de negócio ou feature piecewise (ex.: penalização se TPC < 45).
3. Documentar curva esperada TPC vs. TSA para homologação.

---

### D-15 — Cronograma e escopo de modelos (Redes Neurais)

| Fonte | Modelos |
|---|---|
| **PRD Marco 2** | ElasticNet + Random Forest |
| **PRD Marco 3** | Avaliação paralela de Redes Neurais |
| **Resumo / Testes** | Não mencionam NN |

**Problema:** NN pode conflitar com requisito de explicabilidade e simplicidade do MVP; esforço em setembro não está refletido nos critérios de aceite.

**Impacto:** Dispersão de esforço com dedicação parcial (4 h/dia); modelo final indefinido na homologação.

**Mitigação:**
1. Definir política de seleção: modelo campeão = melhor MAE **desde que** passe testes de monotonicidade e explicabilidade mínima.
2. NN como **experimento opcional** (Marco 3); não bloqueia entrega se RF/ElasticNet atenderem critérios.
3. Critério de desempate: interpretabilidade > complexidade.

---

### D-16 — Volume_m3 como entrada nos testes, papel ambíguo no PRD

| Fonte | Volume |
|---|---|
| **PRD** | Ponderação por volume nas médias de qualidade |
| **TC-01, TC-02** | Volume_m3 > 1.200 e = 1.050 como entrada explícita; ganho por escala no Sítio A |

**Problema:** PRD não lista Volume_m3 como feature preditiva; testes assumem efeito de escala industrial.

**Impacto:** Feature omitida pode impedir reprodução do TC-01.

**Mitigação:**
1. Confirmar se volume diário entra no Elo 3 como feature de escala.
2. Se sim, adicionar ao PRD; se não, revisar TC-01 para remover expectativa de "ganho por economia de escala" ou derivar volume do mix.

---

### D-17 — Filtro operacional (Produção < 1.000 TSA/dia) sem rastreio nos testes

| Fonte | Filtro de treino |
|---|---|
| **PRD** | Excluir registros com Produção_Digestor < 1.000 TSA/dia |
| **Casos de Teste** | Não referenciado |

**Problema:** Regra de limpeza crítica para treino não validada em pipeline nem documentada para homologação.

**Mitigação:**
1. Teste de pipeline de dados: garantir ausência de registros < 1.000 no dataset de treino.
2. Documentar contagem de registros excluídos e impacto no MAE.

---

## 4. Matriz Consolidada de Divergências

| ID | Tema | Severidade | Documentos em conflito | Mitigação resumida |
|---|---|---|---|---|
| D-01 | Faixas DB_LAB | Crítica | PRD vs. Testes | Tabela única validada pelo stakeholder |
| D-02 | Unidades kg/m³ vs. g/cm³ | Crítica | PRD vs. Testes | Padronizar kg/m³ + validação de schema |
| D-03 | Faixas de Extrativos | Crítica | PRD vs. Testes | Zonas ótima/aceitável/crítica unificadas |
| D-04 | Estresse físico (extrativos/TPC) | Alta | PRD vs. Resumo vs. Testes | Expandir critérios PRD + testes monotonicidade |
| D-05 | % Casca na cascata | Alta | PRD vs. Resumo | Decisão de escopo + ajuste de premissa |
| D-06 | Validação por elo da cascata | Alta | PRD vs. Testes | Modos A/B de teste + MAE por elo |
| D-07 | DB_SGF vs. DB_LAB | Alta | PRD interno vs. Testes | Diagrama de conversão por elo |
| D-08 | Variável Kappa | Alta | Testes vs. PRD | Incluir no PRD ou remover dos testes |
| D-09 | Sítios D e MG | Média | PRD vs. Testes | Novos casos TC-06 e TC-07 |
| D-10 | Camada C (entropia/HHI) | Média | PRD vs. Testes | Testes unitários de features |
| D-11 | Explicabilidade | Alta | PRD vs. Resumo vs. Testes | TC-09, TC-10 + entregável definido |
| D-12 | Gestão de desvios vs. RCA | Média | PRD vs. Resumo | Esclarecer MVP = explicabilidade assistida |
| D-13 | Definição numérica do MAE | Alta | Todos | MAE ≤ 56 + matrizes A/B separadas |
| D-14 | Limiar TPC verde | Média | Testes vs. PRD | Formalizar limiar (ex. 45 dias) |
| D-15 | Redes Neurais no cronograma | Média | PRD vs. demais | Política campeão com explicabilidade |
| D-16 | Volume_m3 / escala | Média | Testes vs. PRD | Confirmar feature ou ajustar TC-01 |
| D-17 | Filtro < 1.000 TSA/dia | Baixa | PRD vs. Testes | Teste de pipeline de dados |

---

## 5. Plano de Mitigação Integrado

### Fase 0 — Alinhamento documental (1 semana)

Objetivo: eliminar divergências críticas antes de codificar features ou homologar.

| Ação | Responsável sugerido | Entregável |
|---|---|---|
| Workshop de alinhamento com Thiago Salles | Cientista de Dados + Processo | Ata com faixas DB, Extrativos, TPC, Kappa |
| Publicar tabela de referência operacional | Cientista de Dados | `REFERENCIA_FAIXAS_OPERACIONAIS.md` |
| Atualizar PRD v1.1 com cascata, estresse e MAE numérico | Cientista de Dados | PRD revisado |
| Decisão sobre % Casca (D-05) | Stakeholder | Registro de decisão |
| Revisar casos de teste (unidades, faixas, Kappa) | Cientista de Dados + QA | Casos de Teste v1.1 |

### Fase 1 — Engenharia e validação por elo (Marco 2)

| Ação | Entregável |
|---|---|
| Diagrama de dados PRD → pipeline (DB_SGF/LAB, volume, mix) | Diagrama em `docs/sketch/` |
| Testes unitários Camadas A/B/C do mix | Suite automatizada |
| Métricas MAE por elo + MAE global | Relatório de cascata |
| Modo A (integração) e Modo B (isolamento) na homologação | Protocolo de teste |

### Fase 2 — Homologação (Marco 2–4)

| Ação | Critério de sucesso |
|---|---|
| Matriz A: holdout 2026 | MAE ≤ 56 TSA/dia |
| Matriz B: TC-01 a TC-10 | 100% Pass em monotonicidade e cenários |
| Matriz C: explicabilidade TC-09/TC-10 | Detratores corretos ranqueados |
| Relatório de aderência técnica | Documentação completa (Marco 4) |

---

## 6. Recomendações do Cientista de Dados Sênior

Com base nos pilares da skill de Análise Preditiva aplicados ao GIFI:

### 6.1. Framing e variável-alvo

O problema está bem formulado na direção **abastecimento → TSA**, com restrição correta de remoção de lags. A maior ameaça ao valor de negócio não é o algoritmo escolhido, e sim o **erro composto da cascata** (premissa em aberto do Resumo Técnico). Recomenda-se tratar a cascata como um sistema de três modelos com propagação de incerteza, não como um único modelo de caixa-preta.

### 6.2. Validação

A validação deve ser **temporal** (holdout 2026), **comportamental** (monotonicidade física) e **por elo** (erro de extrativos e carga). Métrica única MAE é necessária, mas insuficiente: um modelo pode ter MAE aceitável violando física em cenários extremos de mix.

### 6.3. Baseline e complexidade

ElasticNet e Random Forest são escolhas adequadas para MVP com explicabilidade. Redes Neurais só se justificam se superarem o campeão nas três matrizes de aceite — não apenas no MAE.

### 6.4. Governança

Antes de qualquer retreinamento ou entrega da interface, os documentos devem convergir nas faixas operacionais (D-01, D-02, D-03). Caso contrário, o simulador será tecnicamente funcional, mas **indefensável** em homologação com negócio e processo.

---

## 7. Próximos Passos Imediatos

1. Agendar sessão de alinhamento com stakeholder para fechar D-01, D-03, D-05, D-08 e D-14.
2. Revisar casos de teste com unidades e faixas corrigidas (D-02).
3. Produzir diagrama único da cascata incluindo DB_SGF/LAB e % Casca (D-05, D-07).
4. Implementar protocolo de homologação com Matrizes A, B e C (D-13, D-11).
5. Registrar versão revisada do PRD e dos casos de teste após alinhamento.

---

## 8. Referências Internas

| Documento | Papel na análise |
|---|---|
| PRD | Fonte primária de requisitos funcionais, features e cronograma |
| Resumo Técnico | KPIs de aceite, premissas em aberto e escopo executivo |
| Casos de Teste | Camada de homologação prática — atualmente com maior divergência numérica |

---

*Documento gerado para apoiar o Marco Zero do Projeto GIFI. Deve ser revisado após workshop de alinhamento com o stakeholder principal.*

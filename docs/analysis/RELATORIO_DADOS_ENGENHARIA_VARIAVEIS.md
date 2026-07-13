# Relatório — Problemas Estruturais de Dados e Pipeline

**Autor:** Emerson Antônio  
**Data:** 2026-07-10  
**Destinatário:** Engenharia de Dados (Camada 2 — Ingest)  
**Base analisada:** `data/l2_excel_validation` (`2026-07-10T07:35:10Z`)  
**Registros:** 7 564 (train 7 064 + holdout 500) | **Período:** 2018-04-01 a 2025-10-30  
**Granularidade publicada:** `(data_processo, turno)`

---

## 1. Objetivo

Descrever problemas estruturais encontrados **apenas** nas variáveis solicitadas para melhoria pela engenharia de dados, com evidências quantitativas, impacto no modelo (MAE Elo 3 / cascata TSA) e recomendações de remediação.

---

## 2. Resumo executivo

| Severidade | Variáveis afetadas | Problema central |
|------------|-------------------|------------------|
| **Crítica** | Extrativo AT, Extrativo Total | **66,7% NA** no histórico; cobertura **assimétrica** train (70% NA) vs holdout (14% NA) |
| **Crítica** | Produção digestor (TSA) | **Ambiguidade semântica** turno vs dia; `TSA_dia` ≈ 1/3 de `tsa_meta_dia` na maioria das linhas |
| **Alta** | Casca, Secura | **35,6%** e **9,6% NA**; esparsidade impede uso estável como feature |
| **Alta** | DB Lab / DB SGF | **8,6%** de `DB_LAB` é proxy (649 linhas); divergência Lab−SGF média **−6,5 kg/m³**; shift holdout **−15 kg/m³** |
| **Alta** | Extrativo SGF | Disponível em **88%** das linhas, mas **não integrado** a AT (ρ ≈ 0,07); 4 085 linhas com SGF sem AT |
| **Média** | Mix (A+B, C, D+MG) | Dados íntegros, porém **shift de regime** no holdout (Δ pct_AB +0,19; Δ pct_DMG −0,15) |
| **Média** | VMI (faixas) | Flags derivadas corretas; **mudança de perfil** no holdout (menos VMI ≤0,21; mais VMI >0,25) |
| **Baixa** | Carga, Kappa, TPC, Idade | Cobertura alta; variação intra-dia coerente com grão turno |

---

## 3. Mapeamento negócio → L2

| Variável de negócio | Coluna L2 | Status no artefato |
|---------------------|-----------|-------------------|
| Produção digestor (tsa/dia) | `TSA_dia` | Publicada |
| Carga alcalina | `Carga_Alcalina` | Publicada |
| Kappa | `Kappa` | Publicada |
| Densidade básica SGF | `DB_SGF` | Publicada |
| Densidade básica Lab | `DB_LAB` | Publicada (+ flag `db_origin`) |
| % Secura cavacos | `Secura_pct` | Publicada |
| % Casca cavacos | `Casca_pct` | Publicada |
| Extrativo total | `Extrativo_Total` | Publicada |
| Extrativo álcool toluol | `Extrativo_AT` | Publicada |
| Extrativo SGF | `Extrativo_SGF` | Publicada |
| TPC | `TPC` | Publicada |
| Idade | `Idade` | Publicada |
| VMI ≤ 0,21 | `vmi_le_021` | Derivada de `VMI` |
| VMI 0,21 a 0,25 | `vmi_021_025` | Derivada de `VMI` |
| VMI > 0,25 | `vmi_gt_025` | Derivada de `VMI` |
| A + B | `pct_AB` | Derivada (`pct_A + pct_B`) |
| C | `pct_C` | Publicada |
| D + MG | `pct_DMG` | Derivada (`pct_D + pct_MG`) |

**Coluna ausente no L2 publicado:** `extr_origin` (prevista no contrato `feature-columns.yaml` para rastrear origem medido/estimado de `Extrativo_AT`).

---

## 4. Análise por grupo

### 4.1 Dados do Processo Industrial (Turno / Média Diária)

#### 4.1.1 Produção digestor (`TSA_dia`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0%** (7 564 / 7 564) |
| Faixa | 3 001 – 3 650 t/dia |
| Média train / holdout | 3 410 / **3 469** (Δ **+58,5 t/dia**) |

**Problemas estruturais**

1. **Ambiguidade turno vs dia:** o contrato define grão `(data_processo, turno)`, mas o rótulo de negócio é “tsa/**dia**”. Na prática:
   - `tsa_meta_dia` é **constante por dia** (valor diário correto).
   - `TSA_dia` **varia entre turnos** no mesmo dia em **1 282 / 2 440 dias** (52%).
   - Em **~6 735 linhas**, `TSA_dia ≈ tsa_meta_dia / 3` (quota por turno), não o valor diário.
   - Apenas **61 / 7 064** linhas de train têm `TSA_dia == tsa_meta_dia`.

2. **Inconsistência no holdout:** padrão turno/dia **diferente** do train (456/500 ≈ 1/3; 10/500 iguais ao meta diário).

3. **Impacto no modelo:** alvo com semântica mista dificulta cascata, agregação e comparabilidade com gate “MAE TSA/dia”. O shift +58 t/dia no holdout amplifica erro de generalização.

**Recomendações ED**

- [ ] Definir oficialmente: alvo é **produção diária** ou **produção alocada por turno**.
- [ ] Se diário: publicar **uma linha por dia** ou replicar `tsa_meta_dia` em todos os turnos com documentação explícita.
- [ ] Se por turno: renomear canônico (`TSA_turno`) e documentar regra de alocação (1/3, ponderado por volume, etc.).
- [ ] Auditar holdout 2025-05→10 — regra de TSA parece distinta do histórico.

---

#### 4.1.2 Carga alcalina (`Carga_Alcalina`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0%** |
| Faixa | 15,8 – 22,0 (% Na₂O eq.) |
| Média train / holdout | 19,65 / **18,11** (Δ **−1,54**) |
| Variação intra-dia | **2 378 / 2 440 dias** com valores distintos entre turnos |

**Problemas estruturais**

1. **Granularidade:** valor muda por turno (esperado se grão = turno), mas Elo 2 trata como feature intermediária na cascata — OK se consistente, porém exige documentação da regra (média ponderada vs medição por turno).

2. **Shift operacional no holdout:** carga média **1,5 p.p.** menor — coerente com faixa crítica documentada (>21) e correlacionada com queda de TSA.

3. **Contrato vs realidade:** `feature-columns.yaml` marca `required_train: false` (esparsa), mas Excel entrega **100% preenchido** — pode ocultar imputações upstream não rastreadas.

**Recomendações ED**

- [ ] Documentar origem (medido vs calculado vs média diária replicada).
- [ ] Adicionar flag de proveniência (`carga_origin`), similar a `db_origin`.
- [ ] Validar se carga por turno é independente ou derivada de valor diário.

---

#### 4.1.3 Kappa (`Kappa`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0,9%** (67 linhas) |
| Faixa | 4,6 – 19,9 |
| Média train / holdout | 16,4 / 15,8 (Δ −0,57) |
| Variação intra-dia | **2 355 / 2 440 dias** |

**Problemas estruturais**

1. **67 linhas sem Kappa** — exclusão pequena, mas sem regra documentada de imputação ou exclusão.

2. **Variação por turno** no mesmo dia — confirmar se é medição real ou artefato de join.

3. **Baixa correlação linear com TSA** (ρ ≈ +0,07) — não é problema de dados, mas expectativa de poder preditivo moderada.

**Recomendações ED**

- [ ] Tratar 67 NA: excluir com log ou imputar com regra explícita.
- [ ] Confirmar unidade e frequência de amostragem de Kappa por turno.

---

### 4.2 Características Físico-Químicas (Lab e SGF)

#### 4.2.1 Densidade básica SGF (`DB_SGF`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0%** |
| Faixa | 450 – 528 kg/m³ |
| Média train / holdout | 491 / **483** (Δ **−7,7**) |

**Problemas estruturais**

1. **Shift no holdout** para valores mais baixos — alinhado à queda de `DB_LAB` e à hipótese de U-shaped (PRD).

2. Sem flag de proveniência (sempre SGF; OK).

**Recomendações ED**

- [ ] Monitorar drift temporal de DB_SGF (alerta se μ holdout − μ train > 10 kg/m³).

---

#### 4.2.2 Densidade básica Lab (`DB_LAB`)

| Indicador | Valor |
|-----------|-------|
| Missing após imputação | **0%** (imputado) |
| Origem `lab` | 6 915 linhas (91,4%) |
| Origem `proxy` | **649 linhas (8,6%)** — `DB_LAB = 0,985 × DB_SGF` |
| Δ médio (Lab − SGF) quando lab | **−6,5 kg/m³** (σ 15,3) |
| Média train / holdout | 484 / **469** (Δ **−15,1**) |

**Problemas estruturais**

1. **Imputação mascara ausência real:** 649 linhas sem medição Lab aparecem como completas; warning `INGEST_PROXY_DB` registrado, mas consumidor downstream não distingue facilmente proxy de lab no holdout.

2. **Divergência Lab vs SGF** significativa (−6,5 kg/m³ em média) — esperado operacionalmente, porém reforça necessidade de manter `db_origin` em features de modelagem.

3. **Maior shift holdout** entre todas as variáveis contínuas (−15,1) — impacto direto no Elo 3 (feature `DB_LAB`).

**Recomendações ED**

- [ ] Nunca descartar `db_origin` na publicação L2.
- [ ] Separar métricas de qualidade: `% proxy` por ano e por holdout.
- [ ] Avaliar modelo de imputação Lab←SGF por período (0,985 fixo pode ser insuficiente).

---

#### 4.2.3 % Secura cavacos (`Secura_pct`)

| Indicador | Valor |
|-----------|-------|
| Missing | **9,6%** (728 linhas) |
| Faixa (observado) | 44 – 107% |
| Média train / holdout | 63,1 / 60,4 (Δ −2,7) |
| NA holdout | **4%** (vs 10% train) |

**Problemas estruturais**

1. **Esparsidade moderada** — variável **não entra** no `elo_specs` atual, mas está disponível para engenharia futura.

2. **Valores > 100%** (máx 107%) — revisar unidade/escala ou erro de cálculo na origem.

3. **NA parcialmente independente de Casca:** 191 linhas com Secura NA mas Casca presente.

**Recomendações ED**

- [ ] Validar faixa física (0–100%).
- [ ] Documentar periodicidade de análise lab de secagem.
- [ ] Harmonizar cobertura Secura ↔ Casca (mesmo lote de amostra?).

---

#### 4.2.4 % Casca cavacos (`Casca_pct`)

| Indicador | Valor |
|-----------|-------|
| Missing | **35,6%** (2 692 linhas) |
| Faixa (observado) | 0,09 – 3,49% |
| Média train / holdout | 0,85 / 0,78 (Δ −0,07 p.p.) |
| NA holdout | **12%** (vs 37% train) |

**Problemas estruturais**

1. **Alta esparsidade no train** — feature **opcional** Elo 3; imputer mediano usado, mas 1/3 NA reduz informação.

2. **Assimetria train/holdout** na cobertura (37% vs 12% NA) — mesmo padrão dos extrativos.

3. **518 linhas** com Secura e Casca ambos NA; coleta lab incompleta.

**Recomendações ED**

- [ ] Priorizar preenchimento de Casca nos anos 2018–2020 (cobertura mínima).
- [ ] Flag `casca_origin` (medido / não amostrado).

---

#### 4.2.5 Extrativo total (`Extrativo_Total`)

| Indicador | Valor |
|-----------|-------|
| Missing | **66,6%** (5 036 linhas) |
| Faixa (observado) | 1,75 – 6,19% |
| Média train / holdout (onde existe) | 3,48 / 3,74 |
| NA train / holdout | **70% / 14%** |

**Problemas estruturais**

1. **Mesma lacuna temporal que Extrativo AT** — sem medição 2018–2020; cobertura parcial 2021–2023; alta cobertura 2024–2025.

2. **Co-missing com AT:** NA counts praticamente idênticos (5 036 vs 5 039) — mesma origem lab.

3. **Relação AT ≤ Total** consistente (0 violações em 2 525 linhas com ambos) — qualidade interna OK quando medido.

**Recomendações ED**

- [ ] Tratar Extrativo Total e AT como **pacote lab** (coleta conjunta).
- [ ] Backfill histórico ou marcar explicitamente “pré-2021 sem protocolo de extrativos”.

---

#### 4.2.6 Extrativo álcool toluol (`Extrativo_AT`)

| Indicador | Valor |
|-----------|-------|
| Missing global | **66,6%** (5 039 linhas) |
| NA train / holdout | **70,3% / 14,4%** |
| Cobertura por ano | 2018–2020: **0%**; 2021: 38%; 2022: 12%; 2023: 39%; 2024: 96%; 2025: 89% |
| Com origem `lab` | 2 496 / 6 915 (**36%**) |
| Com origem `proxy` | 29 / 649 (**4,5%**) |
| SGF presente, AT ausente | **4 085 linhas** |

**Problemas estruturais**

1. **Crítico para cascata:** Elo 1 prevê `Extrativo_AT`; Elo 3 exige coluna preenchida. Com 70% NA no train, restam **~2 097 linhas** com extrativo observado — gargalo principal do MAE.

2. **Assimetria train/holdout:** holdout 2025 tem **86% de cobertura** vs train com **30%** — modelo treinado em subconjunto esparsíssimo é avaliado em regime com muito mais labels (viés de avaliação).

3. **Extrativo SGF não utilizado como ponte:** 4 085 linhas têm SGF mas não AT; correlação AT×SGF **ρ ≈ 0,07** — proxy naïve inviável, mas integração florestal deveria ser documentada.

4. **`extr_origin` ausente** no parquet publicado — impossível auditar medido vs estimado pós-ingest.

**Recomendações ED**

- [ ] **Prioridade 1:** aumentar cobertura lab de AT no histórico (meta: >80% train).
- [ ] Publicar `extr_origin` conforme contrato.
- [ ] Definir política quando só SGF existe: NULL explícito vs estimativa florestal versionada (não silenciosa).
- [ ] Alinhar frequência de amostragem lab com grão turno ou agregar qualidade por dia abastecido.

---

#### 4.2.7 Extrativo SGF (`Extrativo_SGF`)

| Indicador | Valor |
|-----------|-------|
| Missing | **11,7%** (882 linhas) |
| Faixa | 2,78 – 5,93% |
| Média train / holdout | 3,99 / 4,04 |
| NA holdout | **0%** |

**Problemas estruturais**

1. **Cobertura muito superior a AT** (88% vs 33%) — oportunidade perdida de linkage florestal→processo.

2. **Baixa correlação com AT** (ρ ≈ 0,07) — variáveis **não substituíveis**; exigem reconciliação de negócio (SGF planificado vs AT medido).

3. **882 NA** concentrados no train; holdout completo — nova assimetria temporal.

**Recomendações ED**

- [ ] Documentar diferença semântica SGF vs AT para consumidores.
- [ ] Preencher 882 NA ou marcar `extr_sgf_origin`.
- [ ] Avaliar join TI florestal × lab com chave de data abastecimento.

---

### 4.3 Abastecimento, Manejo e Mix

#### 4.3.1 TPC (`TPC`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0%** |
| Faixa | 20 – 211 dias |
| Média train / holdout | 69,3 / **74,2** (Δ +4,9) |
| p50 | 65 dias |

**Problemas estruturais**

1. **Valores extremos** (máx 211 dias) — validar outliers vs regra de faixa crítica (<45 verde, PRD).

2. **Shift moderado no holdout** (+4,9 dias) — mais madeira em pátio longo.

**Recomendações ED**

- [ ] Cap/winsor documentado ou flag `tpc_outlier`.
- [ ] Confirmar se TPC é média ponderada por volume dos talhões (conforme PRD).

---

#### 4.3.2 Idade (`Idade`)

| Indicador | Valor |
|-----------|-------|
| Missing | **0%** |
| Faixa | 5,1 – 10,1 anos |
| Média train / holdout | 6,73 / 6,81 (Δ +0,08) |

**Problemas estruturais**

- **Nenhum crítico.** Estável, completa, sem shift relevante.

**Recomendações ED**

- [ ] Manter como referência de qualidade (benchmark para outras variáveis).

---

#### 4.3.3 VMI ≤ 0,21 / 0,21 a 0,25 / > 0,25

| Flag | Média train | Média holdout | Δ holdout |
|------|-------------|---------------|-----------|
| `vmi_le_021` | 0,121 | 0,058 | **−0,063** |
| `vmi_021_025` | 0,424 | 0,386 | −0,038 |
| `vmi_gt_025` | 0,454 | 0,556 | **+0,102** |

**Problemas estruturais**

1. **Derivação OK:** flags mutuamente exclusivas (100% das linhas soma = 1; 0 inconsistências vs `VMI` contínuo).

2. **Shift de perfil no holdout:** menos cavacos críticos (VMI ≤0,21), mais na faixa ideal (>0,25) — mudança de mix físico do abastecimento.

3. **Flags não estão em `elo_specs`** — apenas `VMI` contínuo entra no Elo 3; bins já prontos não são consumidos.

**Recomendações ED**

- [ ] Manter derivação automática no ingest (funcionando).
- [ ] Expor `VMI` contínuo + flags no contrato de features para modelagem.
- [ ] Documentar se VMI é média ponderada por volume (PRD).

---

#### 4.3.4 A + B (`pct_AB`), C (`pct_C`), D + MG (`pct_DMG`)

| Variável | Missing | Média train | Média holdout | Δ holdout |
|----------|---------|-------------|---------------|-----------|
| `pct_AB` | 0% | 0,604 | **0,797** | **+0,194** |
| `pct_C` | 0% | 0,157 | 0,117 | −0,041 |
| `pct_DMG` | 0% | 0,240 | **0,087** | **−0,153** |

**Validações OK**

- `pct_A + pct_B + pct_C + pct_D + pct_MG = 1,0` (±0,02) em **100%** das linhas.
- `pct_AB = pct_A + pct_B` e `pct_DMG = pct_D + pct_MG` — derivação exata.

**Problemas estruturais**

1. **Shift de mix no holdout:** forte aumento de A+B (+19 p.p.) e queda de D+MG (−15 p.p.) — explica parte do erro de generalização (regime de abastecimento 2025 diferente do histórico).

2. **Granularidade turno:** mix é média dos talhões no abastecimento do turno — OK se documentado; repetido 3×/dia com possível variação.

**Recomendações ED**

- [ ] Publicar série temporal de mix agregada mensal para monitorar drift.
- [ ] Garantir que cenários Modo A replicam a mesma regra de média ponderada.

---

## 5. Problemas transversais de pipeline

| # | Problema | Variáveis impactadas | Evidência |
|---|----------|---------------------|-----------|
| P1 | **Grão turno vs semântica diária** | TSA, Carga, Kappa | `TSA_dia` ≠ `tsa_meta_dia`; 3 turnos/dia em 98% dos dias |
| P2 | **Cobertura assimétrica train/holdout** | Extrativo AT/Total, Casca, Secura | Holdout 2025 muito mais completo que train 2018–2023 |
| P3 | **Lacuna temporal 2018–2020** | Extrativo AT, Extrativo Total | 0% cobertura por 3 anos |
| P4 | **Imputação sem rastreio completo** | DB Lab | Proxy OK; `extr_origin` não publicado |
| P5 | **SGF ≠ AT sem ponte formal** | Extrativo SGF, Extrativo AT | 4 085 linhas despareadas; ρ 0,07 |
| P6 | **Agregação turno→dia não aplicada** (I3) | Qualidade lab, TSA | Ingest doc prevê D-C; artefato permanece turno com inconsistência TSA |
| P7 | **Shift operacional holdout** | TSA, DB, Mix, VMI, TPC | Múltiplas Δμ significativas simultâneas |

---

## 6. Matriz de priorização para engenharia de dados

| Prioridade | Ação | Variáveis | Impacto esperado |
|------------|------|-----------|------------------|
| **P0** | Backfill / protocolo lab Extrativo AT histórico | Extrativo AT, Total | **Alto** — destrava Elo 1 e Elo 3 |
| **P0** | Definir e padronizar semântica TSA (turno vs dia) | TSA | **Alto** — alvo do modelo |
| **P1** | Publicar `extr_origin`; política SGF→AT | Extrativo AT, SGF | **Alto** — auditabilidade |
| **P1** | Harmonizar cobertura Casca/Secura | Casca, Secura | Médio |
| **P1** | Monitorar `% db_origin=proxy` e drift DB | DB Lab, SGF | Médio |
| **P2** | Validar outliers TPC / Secura >100% | TPC, Secura | Baixo–médio |
| **P2** | Série de drift mix/VMI para holdout | Mix, VMI | Médio (explicabilidade) |

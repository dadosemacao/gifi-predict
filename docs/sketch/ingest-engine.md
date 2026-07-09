# Ingest Engine — Plano Macro do Sistema de Ingestão

**Autor:** Emerson Antônio  
**Data:** 2026-07-09  
**Versão:** 1.1  
**Escopo:** Sistema que materializa a Camada 2 da backbone (Dados e Representação)  
**Brief:** `docs/PRD_GIFI_v1.1.md`  
**Backbone:** `docs/sketch/analytical-backbone.md`

> **Nomenclatura canônica (obj. 1):** este arquivo, `ingest-engine.md`, é o **único plano oficial do engine** do GIFI. Qualquer referência a `sentinel-engine.md` é considerada **inexistente/obsoleta** e não deve ser usada. Se um plano de monitoramento/observabilidade for necessário no futuro, será criado como documento próprio e referenciado aqui.

---

## 1. Papel no GIFI

O **Ingest Engine** é o sistema que transforma fontes brutas (Excel QM×Processo, tabelas TI, planilhas de cenário) em **artefatos versionados e auditáveis** que a plataforma determinística consome.

Ele **não** treina modelos nem calcula TSA. Ele garante: schema válido, regras do brief aplicadas, falhas sinalizadas, remediação rastreável.

```
[Fontes brutas] → [Ingest Engine] → [Artefatos L2] → [Backbone Camadas 3–5]
                         ▲
                         │ sinais / logs / contratos
                         └── Backbone Camada 1 (Domínio)
```

### 1.1 Dois caminhos de execução (obj. 6 — natureza batch vs online)

O sistema tem **dois modos operacionais de natureza diferente**, que não compartilham o mesmo SLA:

| Caminho | Natureza | Latência-alvo | Uso |
|---|---|---|---|
| **Ingest Histórico** | **Batch** (lote / quarentena / reprocesso) | minutos–horas; assíncrono | Treino, holdout, features versionadas |
| **Validação de Cenário** | **Online síncrono** (validação leve na hora do upload) | segundos; interativo | UI de simulação (Modo A/B) |

**Regra:** a Validação de Cenário executa **apenas** checagens leves e determinísticas (schema, unidades, soma do mix, faixas) — **sem** quarentena, sem reprocesso, sem remediação humana no loop. O ciclo de remediação (§3) aplica-se **somente ao Ingest Histórico**. Isso evita prometer resposta “instantânea” apoiada em pipeline batch.

---

## 2. Componentes e funções

### I1 — Conectores de fonte

| Função | Detalhe |
|---|---|
| Ler fontes | Base QM×Processo; tabelas limpas/interpoladas da TI (quando houver); template de cenário (Superfície) |
| Identificar lote | Nome, hash, período coberto, timestamp de ingestão |
| Classificar modo | **Histórico** (treino/validação) vs **Cenário** (inferência Modo A/B) |

### I2 — Validação de contrato (schema + domínio)

| Função | Detalhe |
|---|---|
| Schema | Colunas obrigatórias, tipos, unidades (kg/m³, %, dias, m³) |
| Regras do brief | Filtro TSA < 1.000; soma mix ≈ 1,0 (±0,02); faixas DB [350, 650] |
| Separação de modos | Cenário Modo A sem Extrativo/Carga injetados; Modo B permite injeção |

### I3 — Transformação e imputação

| Função | Detalhe |
|---|---|
| Limpeza | Tipagem, nulos controlados, exclusão operacional |
| Imputação DB | `DB_LAB = 0,985 × DB_SGF` quando Lab ausente; marcar origem (`lab` \| `proxy`) |
| Features Mix A/B/C | `pct_*`, `pct_ABC`, `pct_CDMG`, entropy, HHI, `dom_X` |
| Qualidade ponderada | Médias por volume (DB, Extrativo_AT, Casca) |
| Agregação | Turno → dia (regra a fechar; ver pendências) |

### I4 — Publicação de artefatos

| Função | Detalhe |
|---|---|
| Dataset de treino | Tabela versionada pronta para Elo 1/2/3 |
| Dataset de holdout | Partição temporal alinhada à Matriz A |
| Feature table | Representação única para treino, testes TC e inferência |
| Manifesto do lote | Metadados: versão, regras aplicadas, contagens, exclusões |

### I5 — Observabilidade e sinais

| Função | Detalhe |
|---|---|
| Logs estruturados | Início/fim, fonte, linhas lidas/escritas, duração |
| Sinais de falha | Bloqueantes vs avisos (ver §4) |
| Quarentena | Lotes rejeitados isolados, sem publicar artefato “verde” |
| Evidência de remediação | Antes/depois + motivo + responsável |

---

## 3. Ciclo de remediação

Fluxo padrão quando a ingestão falha ou degrada:

```
1. DETECTAR   → sinal (bloqueante ou aviso) + log
2. ISOLAR     → lote em quarentena; backbone não consome artefato novo
3. DIAGNOSTICAR → manifesto + amostra de violação (schema, mix, unidade, nulos)
4. REMEDIAR   → corrigir fonte / regra / mapeamento (humano + reprocesso)
5. REPROCESSAR → novo lote com novo hash/versão
6. PUBLICAR   → só se I2+I3 passarem; sinal OK para backbone
7. REGISTRAR  → evidência no histórico de remediação
```

| Tipo de sinal | Ação | Exemplos |
|---|---|---|
| **Bloqueante** | Não publica; backbone permanece na última versão boa | Schema quebrado; unidade g/cm³; mix fora de ±0,02; DB fora de [350, 650] sem tratamento |
| **Aviso** | Publica com flag; Confiança/Motor decidem uso | Extrativo_AT ausente (esperado no Modo A); Casca nula; cobertura Lab baixa em janela antiga |
| **Informativo** | Segue | Contagem excluída por TSA < 1.000; % proxy DB aplicado |

**Regra:** Camadas 3–5 da backbone **só avançam** sobre artefato com status `published_ok` (ou `published_with_warnings` explicitamente aceito pela Confiança).

### 3.1 Matriz objetiva de warnings admissíveis (obj. 5)

`published_with_warnings` **não é subjetivo**. Cada warning tem admissibilidade **fixa por contexto**:

| Warning | Treino | Holdout (Matriz A) | Inferência/Cenário |
|---|---|---|---|
| `INGEST_PROXY_DB` (DB imputado 0,985×SGF) | **Admitido** (flag obrigatória) | **Admitido** se ≤ 20% das linhas; senão bloqueia | Admitido (marca origem) |
| `INGEST_SPARSE_LAB` (Extrativo/Casca esparsos) | Admitido | **Bloqueia** se alvo/feature crítica ausente na janela | Admitido no Modo A (estimado) |
| `INGEST_FILTER_INFO` (TSA<1.000 removido) | Admitido (info) | Admitido | N/A |
| Demais warnings novos | **Default = bloqueia** até classificação explícita aqui | idem | idem |

**Ponte com as diretrizes:** um artefato só é elegível à Matriz A/B/C se **todos** os seus warnings forem “Admitido” no contexto de uso. Qualquer warning fora desta tabela é tratado como **bloqueante** (alinha com `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` §8 — bloqueio de release). Não existe “aceite ad hoc”.

---

## 4. Interface com a Backbone (contrato explícito)

### 4.1 O que o Ingest **consome** da Backbone

| Origem (Backbone) | Artefato / sinal | Uso no Ingest |
|---|---|---|
| **Camada 1 — Domínio** | Faixas operacionais, fator 0,985, regras de filtro/mix | Contrato de validação (I2/I3) |
| **Camada 1** | Protocolo TC-P01, TC-08, TC-A02 | Critérios de pronto da ingestão |
| **Camada 1** | Definição Modo A vs B | Validação de planilha de cenário |
| **Camada 1 — Domínio** | **Especificação (contrato) do template de cenário**, versionada | Fonte de verdade do schema de upload (ver nota obj. 3) |
| **Camada 4 — Confiança** | Sinal de **rejeição de lote** (dados inválidos descobertos no aceite) | Dispara ciclo de remediação |
| **Camada 4** | Pedido de **reprocesso** (nova janela holdout / correção de agregação) | Novo lote versionado |
| **Camada 5 — Superfície** | **Instância** da planilha de cenário (arquivo enviado pelo usuário) | Dado de entrada do modo Cenário |
| **Camada 5** | Sinal de falha de parse/template | Feedback ao usuário (sem quarentena; validação online §1.1) |

> **Correção (obj. 3 — quebra da circularidade):** o **template de cenário é um artefato da Camada 1 (Domínio)**, não da Camada 5. A UI apenas fornece a **instância** (arquivo preenchido). Assim, o Ingest valida contra um contrato que **já existe antes** da UI, e a construção do conector de cenário (I1 Cenário) não fica bloqueada pela existência da interface. Ordem de bootstrap: Domínio publica `template_cenario_v0` → Ingest valida → UI consome o mesmo contrato.
| **Operação / TI** | Tabelas limpas ou Excel consolidado | Fonte modo Histórico |
| **Operação** | Logs de falha de entrega de fonte | Atraso / retry de I1 |

### 4.2 O que o Ingest **entrega** à Backbone

| Destino (Backbone) | Artefato | Conteúdo mínimo |
|---|---|---|
| **Camada 3 — Motor** | `train_features` / `infer_features` | Features Mix + qualidade + processo; flag origem DB |
| **Camada 3** | Manifesto do lote | Versão, hash fonte, regras, n exclusões |
| **Camada 4 — Confiança** | `holdout_features` | Partição temporal para Matriz A |
| **Camada 4** | Relatório de qualidade do lote | Contagens, % nulos, % proxy DB, violações |
| **Camada 4** | Sinais | `ingest_ok` \| `ingest_warn` \| `ingest_fail` |
| **Camada 5 — Superfície** | Resultado de validação do upload | Aceito / rejeitado + motivo legível |
| **Camada 2 (estado)** | Última versão boa publicada | Fallback se lote novo falhar |

#### Contrato operacional dos artefatos (obj. 4)

Nomes semânticos (`train_features`, etc.) **não bastam**. Todo artefato publicado obedece a este contrato mínimo:

| Elemento | Regra |
|---|---|
| **Chave primária** | `data_processo` + `turno` (histórico); `cenario_id` + `linha` (cenário) |
| **Timestamp de referência** | `data_processo` (não a data de ingestão); holdout e ordenação usam este campo |
| **Versão de schema** | `schema_version` (semver) em todo artefato e no manifesto |
| **Versão de dados** | `dataset_version` + `source_hash` (rastreio ao lote de origem) |
| **Compatibilidade** | Mudança **backward-compatible** = incrementa minor; **breaking** = incrementa major + exige aceite da Camada 4 antes de consumir |
| **Contrato de colunas** | Lista fixa de features + tipos + unidade; coluna nova sem major-bump é **proibida** |
| **Flags de origem** | `db_origin ∈ {lab, proxy}`; `extr_origin ∈ {medido, estimado}` |
| **Join treino↔inferência** | Mesma ordem/tipo de features garantida por `schema_version` idêntico |

**Regra de integração:** a Camada 3 recusa artefato cujo `schema_version` major seja diferente do esperado, evitando join/partição silenciosamente incorretos.

### 4.3 Sinais de falha (catálogo macro)

| Código | Severidade | Significado | Efeito na Backbone |
|---|---|---|---|
| `INGEST_SCHEMA_FAIL` | Bloqueante | Coluna/tipo/unidade inválidos | Motor/Confiança não atualizam |
| `INGEST_MIX_FAIL` | Bloqueante | Soma pct fora da tolerância | Idem |
| `INGEST_UNIT_FAIL` | Bloqueante | Densidade fora da escala kg/m³ | Idem |
| `INGEST_FILTER_INFO` | Info | Linhas removidas TSA < 1.000 | Segue; conta no manifesto |
| `INGEST_PROXY_DB` | Aviso | DB_LAB imputado (0,985×SGF) | Motor usa; relatório registra |
| `INGEST_SPARSE_LAB` | Aviso | Baixa cobertura Extrativo/Casca | Elo 1/1b e Matriz A alertados |
| `INGEST_SOURCE_MISSING` | Bloqueante | Fonte não chegou / ilegível | Sem publicação |
| `INGEST_SCENARIO_REJECT` | Bloqueante | Upload fora do template A/B | UI mostra erro; sem inferência |
| `ACCEPT_DATA_REJECT` | Bloqueante* | Confiança devolve lote | Remediação + reprocesso |

\*Gerado na Backbone (Camada 4), consumido pelo Ingest.

### 4.4 Diagrama da conexão

```
 Camada 1 (contratos) ──────────────────────────────► I2 / I3
 Camada 5 (upload cenário) ──► I1 ──► I2 ──► I3 ──► I4 ──► Camada 3 / 4 / 5
 Fontes históricas ──────────► I1 ─┘              │
                                                  ├─► sinais/logs ──► I5
 Camada 4 (reject/reprocess) ─────────────────────► ciclo remediação
```

---

## 5. Dependências (macro)

| Componente | Depende de | Alimenta |
|---|---|---|
| I1 Conectores | Fontes + **template (contrato da Camada 1)** + instância de upload (Camada 5) | I2 |
| I2 Validação | Camada 1 (contratos) | I3 ou quarentena |
| I3 Transformação | I2 ok + regras Camada 1 | I4 |
| I4 Publicação | I3 ok | Backbone 3, 4, 5 |
| I5 Observabilidade | Todos | Remediação + auditoria |

**Dependência externa crítica:** entrega TI da base interpolada (acelera I1/I3; se ausente, Ingest opera sobre o Excel consolidado).

---

## 6. Ordem de construção

| Ordem | Componente | Entrega macro | Alinha com Backbone |
|---|---|---|---|
| 1 | Contratos de interface (§4) | Catálogo de sinais + manifesto | Camada 1 |
| 2 | I2 Validação | Schema + regras brief | Camada 2 início |
| 3 | I1 Conectores (histórico) | Leitura Excel / tabelas TI | Marco 1 |
| 4 | I3 Transformação + imputação | Features Mix A/B/C + proxy DB | Camada 2 |
| 5 | I4 Publicação | Artefatos versionados `published_ok` | Desbloqueia Camada 3 |
| 6 | I5 Logs + remediação | Ciclo detect→remediar→republicar | Operação contínua |
| 7 | I1 Cenário (upload) | Validação template A/B | Camada 5 (UI) |

**Caminho crítico:** `contratos → I2 → I1 histórico → I3 → I4` (sem isso a Backbone Camada 3 não parte).  
**Paralelo tardio:** conector de cenário (passo 7) junto da UI.

---

## 7. Critérios de pronto (macro)

| Item | Pronto quando |
|---|---|
| Ingest histórico | Publica dataset com manifesto; TC-P01 / TC-A02 / TC-08 atendíveis |
| Sinais | Catálogo §4.3 emitido e consumível pela Confiança |
| Remediação | Lote ruim não sobrescreve última versão boa |
| Ingest cenário | Upload inválido rejeitado com motivo; válido vira `infer_features` |
| Interface Backbone | Camada 3 só treina/infere sobre `published_ok` (ou warn aceito) |

---

## 8. Relação com o brief (PRD)

| Requisito PRD | Onde no Ingest |
|---|---|
| §3.1 Fonte e granularidade | I1 + I3 (turno→dia) |
| §3.2 Filtros / kg/m³ / 0,985 / mix | I2 + I3 |
| §3.3–3.4 Mix e ponderação | I3 |
| §3.5 Faixas | I2 (alerta/bloqueio) |
| TC-P01, TC-08, TC-A02 | Aceite de I2–I4 |
| Modos A/B | I2 cenário + entrega a Camada 3 |

---

## 9. Decisões provisórias e pendências

> Alinhado a `analytical-backbone.md` §6. Defaults destravam o build; confirmação é change request.

### 9.1 Decisões fechadas

| Tema | Decisão | Status |
|---|---|---|
| Janela do holdout (partição em I4) | 2025-05 a 2025-10 (holdout); treino até 2025-04 | **Confirmada** (stakeholder, 2026-07-09) |
| Elo 1b (% Casca) | NO-GO no MVP; casca só como feature Elo 3 quando medida | **Confirmada** (stakeholder, 2026-07-09) |
| Agregação turno→dia | Média ponderada por volume (qualidade); soma (volume); TSA meta diária | Assumida (CD) |
| Template de cenário | Contrato v0 publicado pela Camada 1 (Domínio) | Assumida (CD) |
| Formato físico dos artefatos | **Parquet** para datasets; JSON para manifesto | Assumida (CD) |

Registro completo: `DECISOES_GIFI.md`.

### 9.2 Pendências abertas

| Pendência | Responsável | Bloqueia build? |
|---|---|---|
| SLA de reprocesso quando TI republicar base | TI + CD | Não |
| Entrega TI da base interpolada | TI Veracel/Keyrus | Não (fallback Excel) |

---

## 10. Rastreio

| Documento | Papel |
|---|---|
| `analytical-backbone.md` | Plataforma que **consome** os artefatos deste plano |
| `PRD_GIFI_v1.1.md` | Regras de dados e aceite |
| `REFERENCIA_FAIXAS_OPERACIONAIS.md` | Limiares de validação |
| `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | TC de pipeline / features |
| Este arquivo | Plano macro do sistema de ingestão |

---

*Nível macro. Sem tarefas atômicas e sem código. A conexão Ingest ↔ Backbone fica no contrato de artefatos e sinais da §4.*

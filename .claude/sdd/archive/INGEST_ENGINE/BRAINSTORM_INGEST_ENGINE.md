# BRAINSTORM: Ingest Engine — Melhorias e Alinhamento

> Sessão exploratória pós-KB/agentes para fechar gaps antes de /define

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | INGEST_ENGINE |
| **Date** | 2026-07-10 |
| **Author** | Emerson Antônio (brainstorm-agent + gifi-ingest-engineer + gifi-domain-specialist) |
| **Status** | Shipped |

---

## Initial Idea

**Raw Input:** Analisar `docs/sketch/ingest-engine.md` e todas as referências diretas, usando agentes especialistas, e mostrar o que pode ser melhorado.

**Context Gathered:**
- KBs `gifi-domain`, `gifi-ingest`, `spreadsheet-connectors` publicadas (v0.1–0.2)
- Agentes `gifi-domain-specialist`, `gifi-ingest-engineer` criados e roteados
- `feature-columns.yaml` fecha gap I4 da reanálise; P1 ainda pendente (evidência remediação, logging)
- Plano ingest v1.1 é macro e coerente na maior parte; restam inconsistências internas e cross-doc
- `template_cenario_v0` referenciado mas **sem artefato físico** no repositório

**Technical Context Observed:**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `src/ingest/` (a definir no DESIGN) | Separar batch vs online desde o início |
| Relevant KB Domains | gifi-domain, gifi-ingest, spreadsheet-connectors | Fonte normativa para I2–I5 |
| AgentSpec reuse | data-contracts-engineer, data-quality-analyst, python-developer, test-generator | Sem novos agentes de ingest |
| IaC Patterns | N/A no MVP local; Airflow tardio | Orquestração batch só após I4 estável |

---

## Discovery Questions & Answers

| # | Question | Answer (inferida do contexto + docs) | Impact |
|---|----------|--------------------------------------|--------|
| 1 | Qual o objetivo imediato desta análise? | Fechar gaps documentais e P1 KB antes de /define e build | Priorizar alinhamento > código |
| 2 | O dual-path (batch vs online) está claro o suficiente? | Sim em §1.1; falta SLA numérico online e limite de linhas upload | Define precisa quantificar |
| 3 | Template de cenário: quem é dono? | Camada 1 (D-E fechada); backbone Camada 5 ainda lista template como recurso | Corrigir backbone + publicar v0 |
| 4 | Elo 1b no MVP? | NO-GO (D-B); sinais ainda citam 1b | Remover referências obsoletas |
| 5 | Samples disponíveis para grounding? | Excel QM×Processo (TI); sem template preenchido nem ground truth ingest no repo | Bloqueia testes I1 realistas |

**Sample Data Inventory:**

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | TI Excel (externo) | 0 no repo | Fallback documentado |
| Output examples | N/A | 0 | Parquet/manifesto ainda não gerados |
| Ground truth | `CASOS_TESTE_FUNCIONAIS_GIFI_v1.1.md` | TC-P01, TC-08, TC-A02 | Aceite de I2–I4 |
| Related code | N/A | 0 | Fase documental |
| Template cenário | `domain-rules.yaml` (id only) | 0 arquivo | **Gap bootstrap** |

---

## Divergências e Melhorias Identificadas

### P0 — Corrigir antes de /define (risco de build errado)

| ID | Onde | Problema | Correção proposta |
|----|------|----------|-------------------|
| D-ING-01 | `ingest-engine.md` §2 I1 | "template de cenário (Superfície)" | "instância de cenário (Camada 5); contrato template (Camada 1)" |
| D-ING-02 | `ingest-engine.md` §2 I3 | "Agregação turno→dia (regra a fechar)" | Remover pendência; apontar D-C fechada (§9.1) |
| D-ING-03 | `ingest-engine.md` §4.1 L140–141 | Markdown quebrado (nota obj.3 colada na tabela) | Separar blockquote da linha da tabela |
| D-ING-04 | `ingest-engine.md` §4.3 | `INGEST_SPARSE_LAB` → "Elo 1/1b" | "Elo 1 e Matriz A" (1b fora do MVP) |
| D-ING-05 | `analytical-backbone.md` § Camada 5 | "Template de cenário" como recurso da UI | Mover para Camada 1; Camada 5 só "instância upload" |
| D-ING-06 | Repo | `template_cenario_v0` inexistente | Publicar spec YAML/CSV v0 em `docs/kb/gifi-domain/specs/` ou `templates/` |

### P1 — Extensões KB (reanálise já mapeou)

| Artefato | Motivo |
|----------|--------|
| `gifi-ingest/specs/remediation-evidence.yaml` | §3 passo 7 / I5 auditoria antes/depois |
| `gifi-ingest/patterns/structured-logging.md` | Campos mínimos I5 (correlação lote, duração, contagens) |
| `ingest-engine.md` §2 I3 | Mencionar `pct_AB`/`pct_DMG` além de ABC/CDMG (alinhado ao YAML) |

### P2 — Clarificações de design (não bloqueiam doc fix)

| Tema | Gap | Sugestão |
|------|-----|----------|
| Coluna `Sitio` | TC-A01 cita Sítio; `feature-columns.yaml` usa mix `pct_*` | Documentar: Elo 1 usa mix + idade; "sítio" em TC = perfil de mix, não coluna categórica |
| SLA online | "segundos" sem número | Default: p95 < 3s até 500 linhas cenário |
| Paths físicos | Parquet/JSON sem layout de diretório | `artifact-contract.yaml` + path pattern em DESIGN |
| Grain diário | `grain.historical` = turno; holdout diário? | Explicitar artefato `train_features_daily` vs turno no DESIGN |
| `ACCEPT_DATA_REJECT` | Camada 4 → Ingest | Fluxo de reprocesso: quem dispara I1 (evento vs job manual) |

---

## Approaches Explored

### Approach A: Sprint de Alinhamento Documental ⭐ Recommended

**Description:** Corrigir P0 nos 3 docs sketch + publicar `template_cenario_v0` + completar P1 KB antes de qualquer código.

**Pros:**
- Elimina ambiguidade que causou divergências v1.0
- Desbloqueia I1 cenário e validação online com contrato real
- Baixo custo; alto retorno em previsibilidade

**Cons:**
- Atrasa código em ~1–2 dias
- Exige revisão cruzada backbone ↔ ingest ↔ KB

### Approach B: Define/Design Direto com Estado Atual

**Description:** Ir para `/define` agora e tratar inconsistências como "notas de implementação".

**Pros:**
- Velocidade aparente

**Cons:**
- Risco de implementar template na Camada 5 por engano
- Agregação turno→dia pode ser reaberta sem querer
- Drift entre plano §2 e KB YAML

### Approach C: Protótipo I2+I3 sobre Excel Antes de Docs

**Description:** Validar hipóteses com script Python e retroalimentar docs.

**Pros:**
- Evidência empírica de schema real do Excel TI

**Cons:**
- Viola ordem backbone (contratos → dados)
- Sem template v0, cenário online fica de fora

---

## YAGNI — Removido ou Adiado do MVP Ingest

| Item | Decisão | Motivo |
|------|---------|--------|
| Novos agentes/KBs ingest | **Não criar** | Reanálise confirma cobertura |
| Airflow / DAG batch | **Adiar** | I4 manual/local suficiente para Marco 1 |
| Quarentena no path online | **Não** | Já excluído em §1.1 |
| Elo 1b no catálogo de sinais | **Remover** | D-B NO-GO |
| SLA reprocesso TI | **Adiar** | Pendência §9.2 não bloqueia |
| NN / Caminho da Volta | **Fora** | PRD congelado |

---

## Draft Requirements (entrada para /define)

1. **FR-ING-01:** Ingest histórico publica `train_features`, `holdout_features`, `batch_manifest` em Parquet+JSON com `schema_version` semver.
2. **FR-ING-02:** Validação online rejeita upload fora de `template_cenario_v0` em < 3s (500 linhas).
3. **FR-ING-03:** Warning matrix §3.1 implementada literalmente; default desconhecido = bloqueia.
4. **FR-ING-04:** Remediação preserva última versão `published_ok` em falha.
5. **FR-ING-05:** TC-P01, TC-08, TC-A02 verificáveis a partir dos artefatos L2.
6. **NFR-ING-01:** Logs estruturados por lote com `source_hash`, duração, linhas in/out.
7. **NFR-ING-02:** Evidência de remediação com antes/depois, motivo, responsável, timestamp.

---

## Validation Checkpoints

- [x] Checkpoint 1: Divergências P0 listadas e priorizadas
- [x] Checkpoint 2: Abordagem A recomendada; B e C descartadas para MVP
- [x] Checkpoint 3: Sprint P0+P1 executado (2026-07-10)

---

## Next Step

```
/define .claude/sdd/features/BRAINSTORM_INGEST_ENGINE.md
```

Agentes sugeridos na fase Define/Design:
- `gifi-domain-specialist` — template v0, Modo A/B, decisões D-C/D-E
- `gifi-ingest-engineer` — I1–I5, artefatos, sinais
- `data-contracts-engineer` — ODCS formal se necessário
- `test-generator` — fixtures TC-P01/08/A02

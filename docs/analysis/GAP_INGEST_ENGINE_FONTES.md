# Gap Analysis — Ingest Engine (plano × fontes)

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.0  
**Plano:** `docs/sketch/ingest-engine.md` v1.2  
**Código:** `src/ingest/`, `src/serving/` (path online), `src/simulation/l2/` (consumo)  
**KB:** `docs/kb/gifi-ingest/`  
**Ship Marco 1:** `.claude/sdd/archive/INGEST_ENGINE/SHIPPED_2026-07-10.md`

---

## 1. Veredito

O Ingest Engine **Marco 1 está shipped e operacional** (I1–I5, dual-path batch/online, Parquet+manifesto, Excel real validado). Os gaps abaixo **não reabrem o Marco 1**; são débitos de contrato de sinais, rastreabilidade e fechamento de TCs E2E (Marco 2).

| Pergunta | Resposta |
|----------|----------|
| O plano §6 (caminho crítico) está no código? | **Sim** — `contratos → I2 → I1 hist → I3 → I4 → I5 → I1 cenário` |
| Dual-path §1.1 respeitado? | **Sim** — batch com quarentena; online sem remediação no loop |
| Catálogo §4.3 completo na emissão? | **Não** — `INGEST_SOURCE_MISSING` nunca é emitido |
| Critérios de pronto §7 | **Pass com ressalvas** (sinais + ATs E2E parciais) |

**Confidence:** 0.88 (cruzamento plano × módulos `src/ingest/*` × specs YAML × SHIPPED).

---

## 2. Status por path

| Path | Status | Evidência |
|------|--------|-----------|
| Ingest histórico (batch) | Funcional | `src/ingest/batch/pipeline.py`; `tests/ingest/test_batch_pipeline.py`; Excel 7.573 linhas |
| Validação de cenário (online) | Funcional | `src/ingest/online/*` + `src/serving/routes/scenario.py` |
| Separação de SLA | Respeitada | Quarentena só no batch; online não entra no ciclo §3 |
| Conector TI interpolada | Stub | `src/ingest/connectors/ti_stub.py` → `NotImplementedError`; fallback Excel |

---

## 3. Cobertura I1–I5

### I1 — Conectores

| Item do plano | Status | Fonte |
|---------------|--------|-------|
| Excel QM×Processo + lote (nome/hash/período) | OK | `connectors/excel_qm.py` |
| Upload cenário | OK | `connectors/scenario_upload.py` |
| Classificação histórico vs cenário | OK | Entry points distintos (`run_batch_pipeline` / `validate_scenario_file`) |
| Tabelas TI limpas/interpoladas | Stub | `ti_stub.py` |
| `INGEST_SOURCE_MISSING` ao falhar leitura | Falta | `FileNotFoundError` bruto; sinal inexistente em `src/` |

### I2 — Validação

| Item do plano | Status | Fonte |
|---------------|--------|-------|
| Schema + aliases | OK | `validation/schema.py` + `feature-columns.yaml` |
| Mix ±0,02; unidades; DB [350, 650] | OK | `validation/domain_rules.py` |
| Template Modo A/B | OK | `validation/scenario.py` |
| Matriz de warnings (§3.1) | Parcial | `validation/warnings.py` + `warning-matrix.yaml` — bug `admit_mode_a_estimated` |
| Warning desconhecido = bloqueia | OK | `apply_unknown_guard` |

### I3 — Transformação

| Item do plano | Status | Fonte |
|---------------|--------|-------|
| Proxy DB 0,985×SGF + `db_origin` | OK | `transform/imputation.py` |
| Features Mix + entropy/HHI/`dom_*` | OK | `transform/mix_features.py` |
| Filtro TSA < 1.000 | OK | `transform/pipeline.py` (`INGEST_FILTER_INFO`) |
| Agregação turno→dia (qualidade ponderada por volume) | Parcial | `aggregation.py` só adiciona `tsa_meta_dia`; grain turno preservado |
| Imputação Extrativo (extensão pós-plano) | Extra OK | `INGEST_PROXY_EXTR` + `extr_origin` |

### I4 — Publicação

| Item do plano | Status | Fonte |
|---------------|--------|-------|
| `train_features` / `holdout_features` Parquet | OK | `publish/publisher.py`, `parquet_writer.py` |
| Holdout 2025-05..2025-10 | OK | `publish/holdout.py` + `config/ingest.yaml` |
| Manifesto JSON | OK | `publish/manifest.py` |
| Last-good (`current.json`) sem sobrescrever em fail | OK | pointer só em publish elegível |
| `infer_features` (cenário) | OK | `online/infer_publish.py` |
| `ingest_ok` \| `ingest_warn` \| `ingest_fail` no pointer | Parcial | `aggregate_status()` existe; **não gravado** em `current.json` |
| `source_hash` no manifesto de cenário | Falta | manifesto guarda path temp, não hash |

### I5 — Observabilidade / remediação

| Item do plano | Status | Fonte |
|---------------|--------|-------|
| Logs estruturados início/fim | OK | `observability/logging.py` |
| Quarentena de lote | OK | `observability/quarantine.py` |
| Evidência de remediação | OK | `observability/remediation.py` + CLI `reprocess` |
| Amostra de violação na quarentena | Parcial | `sample_violations` sempre vazio no call do batch |
| `ACCEPT_DATA_REJECT` (Camada 4 → Ingest) | Parcial | trigger por arquivo JSON; sem API |
| `max_retries` no batch | Falta uso | config=3; não aplicado em `run_batch_pipeline` |

---

## 4. Catálogo de sinais §4.3

| Código | Emitido no código? | Observação |
|--------|-------------------|------------|
| `INGEST_SCHEMA_FAIL` | Sim | schema + faixas DB (faixa reutiliza código estrutural) |
| `INGEST_MIX_FAIL` | Sim | |
| `INGEST_UNIT_FAIL` | Sim | |
| `INGEST_FILTER_INFO` | Sim | |
| `INGEST_PROXY_DB` | Sim | |
| `INGEST_SPARSE_LAB` | Sim | admissibilidade inference quebrada (ver P0-2) |
| `INGEST_SOURCE_MISSING` | **Não** | só no YAML/catálogo |
| `INGEST_SCENARIO_REJECT` | Sim | online + serving |
| `ACCEPT_DATA_REJECT` | Consumido | via `triggers/`; gerado na Camada 4 |
| `INGEST_PROXY_EXTR` | Sim (extensão) | em `signal-catalog.yaml`; fora do §4.3 original |

### Bug confirmado — warning matrix

Em `warning-matrix.yaml`:

```yaml
INGEST_SPARSE_LAB:
  inference: admit_mode_a_estimated
```

`WarningMatrixEvaluator.is_admitted()` só reconhece `admit` | `not_applicable` | `block` | dict. A string `admit_mode_a_estimated` cai no `return False` → **bloqueia** Modo A com Extrativo esparso, contrariando o plano §3.1 (“Admitido no Modo A”).

---

## 5. Critérios de pronto §7

| Critério | Resultado | Nota |
|----------|-----------|------|
| Histórico publica dataset + manifesto | PASS | Excel real `published_with_warnings` |
| Sinais §4.3 emitidos e consumíveis | FAIL parcial | falta `INGEST_SOURCE_MISSING`; bug SPARSE_LAB |
| Remediação sem sobrescrever last-good | PASS | |
| Cenário inválido rejeitado; válido → `infer_features` | PASS | |
| Backbone só consome publish válido | PASS | `current.json` + guards L3 |

ATs E2E AT-011/012/014/017: **parcial** (Marco 2 no SHIPPED).

---

## 6. Pendências priorizadas

### P0 — contrato / correção funcional

| ID | Gap | Onde | Ação |
|----|-----|------|------|
| P0-1 | `INGEST_SOURCE_MISSING` nunca emitido | `excel_qm.py` + `batch/pipeline.py` | Capturar ausência de fonte; emitir sinal; quarentenar/retornar fail |
| P0-2 | `admit_mode_a_estimated` bloqueia inferência | `warning-matrix.yaml` e/ou `warnings.py` | Alinhar a `admit` ou tratar o valor semântico no evaluator |

### P1 — rastreabilidade

| ID | Gap | Onde | Ação |
|----|-----|------|------|
| P1-1 | `aggregate_status` fora de `current.json` | `publisher.py` / manifesto | Expor `ingest_ok`/`warn`/`fail` no pointer |
| P1-2 | Agregação D-C incompleta (qualidade ponderada) | `aggregation.py` | Confirmar consumo L3; se dia, implementar médias ponderadas |
| P1-3 | `source_hash` ausente no cenário | `infer_publish.py` | Hash do upload no `scenario_manifest.json` |

### P2 — dívida / Marco 2

| ID | Gap | Ação |
|----|-----|------|
| P2-1 | `sample_violations` vazio | Coletar amostra ao quarentenar |
| P2-2 | `max_retries` morto no batch | Retry de I/O na leitura |
| P2-3 | Faixa DB como `INGEST_SCHEMA_FAIL` | Código dedicado ou mensagem tipada |
| P2-4 | `df.attrs["schema_version"]` não persiste em Parquet | Remover dead code ou metadata PyArrow |
| P2-5 | Conector TI real | Aguardar entrega TI (§9.2 do plano) |
| P2-6 | ATs E2E 011/012/014/017 | Suite Marco 2 |
| P2-7 | Trigger `ACCEPT_DATA_REJECT` só por arquivo | API/callback se operação multi-host |

### Externas (plano §9.2)

| Pendência | Bloqueia build? |
|-----------|-----------------|
| Base interpolada TI | Não (fallback Excel) |
| SLA de reprocesso TI | Não |

---

## 7. O que NÃO falta (Marco 1)

Para evitar retrabalho: dual-path, Excel histórico, proxy DB, mix features, holdout temporal, publicação atômica, last-good, quarentena, remediação básica, validação online A/B, CLI `ingest`, consumo L3 via `current.json` + guarda de `schema_version` major, KB de contratos (`signal-catalog`, `warning-matrix`, `artifact-contract`, `feature-columns`).

A reanálise KB (`docs/kb/REANALISE_INGEST_COBERTURA.md`) permanece válida: **não faltam KBs/agentes novos** — faltam fechamentos de código acima.

---

## 8. Rastreio

| Artefato | Papel |
|----------|-------|
| `docs/sketch/ingest-engine.md` | Plano macro |
| `.claude/sdd/archive/INGEST_ENGINE/SHIPPED_2026-07-10.md` | Marco 1 entregue |
| `docs/kb/REANALISE_INGEST_COBERTURA.md` | Gap KB/agentes (fechado) |
| Este arquivo | Gap plano × fontes (código) |

---

*Documento de análise. Sem implementação. Próximo passo sugerido: fechar P0-1 e P0-2.*

# DEFINE: Serving SQLite Audit

> Persistir cada chamada HTTP do GIFI Serving em SQLite para rastreabilidade, auditoria e analytics via SQL.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SERVING_SQLITE_AUDIT |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio |
| **Status** | ✅ Shipped |
| **Clarity Score** | 15/15 |

---

## Problem Statement

O GIFI Serving (`/api/forecast`, `/api/predict-tsa`, `/api/simulate`, etc.) responde predições e simulações sem registrar chamada a chamada o que entrou, o que saiu, qual modelo foi usado e quais campos foram imputados (`medido` / `proxy` / `estimado`). Isso impede reproduzir incidentes, auditar decisões do modelo e medir uso ou drift ao longo do tempo.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Engenheiro de dados / ML | Opera predições e debug | Não consegue recuperar payload de uma chamada Postman/UI após o fato |
| Stakeholder / auditoria | Valida uso do sistema | Sem trilha imutável de inputs, outputs e origem dos campos |
| Analista de produto | Monitora qualidade | Não agrega volume por endpoint, taxa de proxy/estimado ou erros 422 |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Gravar **100%** das requisições `/api/*` (sucesso e erro) com timestamp UTC |
| **MUST** | Persistir request e response (ou `detail` de erro) em JSON |
| **MUST** | Extrair e armazenar `field_origins`, `warnings`, `metrics`, `model_id`, `family` quando presentes |
| **MUST** | SQLite como **SSOT permanente** consultável via SQL |
| **SHOULD** | CLI ou script de consultas comuns (`scripts/audit_query.py`) |
| **SHOULD** | Latência adicional de escrita **≤ 10 ms** p95 em ambiente local |
| **COULD** | Rota read-only `GET /api/audit/calls` (Fase 2) |
| **COULD** | Views analíticas (`v_daily_volume`, `v_proxy_rate`) (Fase 2) |

---

## Success Criteria

- [ ] Toda chamada `POST /api/forecast` bem-sucedida gera **1 linha** em `api_calls` com `status_code=200`, `request_json` e `response_json` não nulos
- [ ] Chamada `POST /api/predict-tsa` com campos omitidos (Tier A/B) persiste `field_origins_json` com valores `proxy`/`estimado`
- [ ] Erro `422` (validação) persiste `status_code=422` e corpo de erro em `response_json`
- [ ] `GET /api/release-status` persiste registro com `product=status` e duração em ms
- [ ] `POST /api/simulate` persiste **hash SHA-256 do arquivo**, `mode`, `row_count` — não o CSV inteiro (MVP)
- [ ] Consulta SQL `SELECT COUNT(*) FROM api_calls WHERE ts_utc >= datetime('now','-1 day')` retorna volume correto após bateria de testes
- [ ] Zero perda de registros em 100 requests sequenciais de teste de integração
- [ ] Overhead p95 de escrita audit **≤ 10 ms** (medido em teste local)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Forecast happy path | DB vazio, serving ativo | `POST /api/forecast` com payload válido | 1 row; `endpoint=forecast`; `status_code=200`; `metrics_json` contém `mae_holdout` |
| AT-002 | Predict-tsa com proxy | Payload sem `db_lab` | `POST /api/predict-tsa` | `field_origins_json.db_lab = "proxy"`; warning persistido |
| AT-003 | Erro validação | Payload sem `carga_alcalina` | `POST /api/predict-tsa` | `status_code=422`; `response_json` contém `detail` |
| AT-004 | Simulate multipart | CSV de cenário válido | `POST /api/simulate` | Row com `file_sha256`, `mode`, `row_count`; sem blob CSV |
| AT-005 | Status GET | — | `GET /api/forecast/status` | Row com `method=GET`; `duration_ms > 0` |
| AT-006 | Idempotência de schema | DB existente | Restart do serving | Migrations idempotentes; sem erro |
| AT-007 | Consulta CLI | ≥5 calls gravadas | `python scripts/audit_query.py --last 5` | Lista 5 IDs com ts, endpoint, status |

---

## Out of Scope

- Dashboard web de observabilidade (Fase 2)
- Armazenamento do arquivo CSV completo em simulate (MVP: hash + metadados)
- Migração para PostgreSQL ou outro banco
- Retenção automática / TTL / purge
- Autenticação, RBAC ou multi-tenant
- OpenTelemetry / tracing distribuído
- Anonimização LGPD (sem PII identificada nos payloads atuais)

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Technical | SQLite 3, WAL mode, arquivo em `logs/serving_audit.db` (configurável) | Single-writer; backup por cópia de arquivo |
| Technical | Python 3.12, FastAPI existente | Middleware ASGI |
| Technical | Escrita **síncrona** na mesma thread | Integridade audit > throughput |
| Architecture | SSOT permanente | Schema versionado em `database/serving_audit/` |
| Project | PT-BR em docs; autor/data em arquivos novos | CHANGELOG após build |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `src/serving/observability/` | middleware, repository, models |
| **SQL Migrations** | `database/serving_audit/` | `001_init.sql` |
| **Config** | `config/serving.yaml` | `audit_db_path`, `audit_enabled` |
| **KB Domains** | gifi-ingest (proveniência), serving | `extr_origin`, `db_origin` como precedente |
| **IaC Impact** | None | Arquivo local |

---

## Data Contract

### Source Inventory

| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| HTTP requests `/api/*` | FastAPI | Dezenas–centenas/dia (dev) | Tempo real | Serving |
| Response bodies | JSON Pydantic | 1:1 com request | Tempo real | Serving |

### Schema Contract — tabela `api_calls`

| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| `id` | TEXT | PRIMARY KEY (UUID) | No |
| `ts_utc` | TEXT | NOT NULL, ISO8601 UTC | No |
| `method` | TEXT | NOT NULL | No |
| `path` | TEXT | NOT NULL | No |
| `endpoint` | TEXT | NOT NULL, normalizado | No |
| `status_code` | INTEGER | NOT NULL | No |
| `duration_ms` | REAL | NOT NULL | No |
| `client_ip` | TEXT | nullable | No |
| `user_agent` | TEXT | nullable | No |
| `product` | TEXT | nullable | No |
| `model_id` | TEXT | nullable | No |
| `family` | TEXT | nullable | No |
| `run_id` | TEXT | nullable | No |
| `request_json` | TEXT | nullable (JSON) | No |
| `response_json` | TEXT | nullable (JSON) | No |
| `field_origins_json` | TEXT | nullable (JSON) | No |
| `warnings_json` | TEXT | nullable (JSON array) | No |
| `metrics_json` | TEXT | nullable (JSON) | No |
| `file_sha256` | TEXT | nullable (simulate) | No |
| `file_name` | TEXT | nullable | No |
| `row_count` | INTEGER | nullable | No |
| `mode` | TEXT | nullable (A/B) | No |
| `error_detail` | TEXT | nullable | No |

**Índices:** `ts_utc`, `endpoint`, `status_code`, `product`

### Freshness SLAs

| Layer | Target | Measurement |
|-------|--------|-------------|
| Persistência | INSERT antes de fechar response | Row existe antes do client receber body |
| Consulta | Imediata pós-commit | SELECT retorna row |

### Completeness Metrics

- 100% das requests `/api/*` com registro (incluindo 4xx/5xx)
- Campos JSON parseáveis em 100% dos happy-path de forecast/predict-tsa

### Lineage Requirements

- `field_origins_json` espelha resposta API (`medido` / `proxy` / `estimado`)
- `model_id` + `family` rastreiam artefato bindado na chamada

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | Volume < 10k calls/dia no horizonte MVP | SQLite single-file suficiente | [ ] |
| A-002 | Payload JSON médio < 50 KB | Tamanho DB controlável | [ ] |
| A-003 | Um processo uvicorn por instância | WAL + single writer OK | [ ] |
| A-004 | Sem PII nos payloads de processo | Sem anonimização MVP | [x] revisão schemas |

---

## Clarity Score Breakdown

| Element | Score | Notes |
|---------|-------|-------|
| Problem | 3 | Dor clara; gap atual documentado |
| Users | 3 | Três personas com pain points |
| Goals | 3 | MUST/SHOULD/COULD priorizados |
| Success | 3 | Métricas numéricas e testáveis |
| Scope | 3 | Out of scope explícito |
| **Total** | **15/15** | |

---

## Open Questions

Nenhuma — pronto para Design.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1 | 2026-07-13 | Emerson Antônio | Shipped and archived |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_SERVING_SQLITE_AUDIT.md`

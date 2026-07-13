# BRAINSTORM: Serving SQLite Audit

> Observabilidade call-by-call do GIFI Serving via SQLite SSOT

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SERVING_SQLITE_AUDIT |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio |
| **Status** | ✅ Shipped |

---

## Initial Idea

**Raw Input:** Construir base SQLite que armazene todos os dados de entrada e saída, observações do modelo, chamada por chamada, com data/hora — rastreabilidade e observabilidade máxima.

**Context Gathered:**
- Serving expõe `/api/forecast`, `/api/predict-tsa`, `/api/simulate`, `/api/scenario/validate`, `/api/release-status`, `/api/template`
- Respostas incluem `field_origins`, `warnings`, `metrics`, `model_id`, `family`
- `resolve_process_fields()` aplica Tier A (proxy) e Tier B (estimado)
- Simulação já usa JSONL em `logs/simulation/`; serving HTTP não persiste calls
- Fixtures em `tests/serving/` e `base/primeira_base.csv`

**Technical Context Observed:**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `src/serving/observability/`, `database/serving_audit/` | Middleware + migrations |
| Relevant KB Domains | gifi-ingest (signals), serving | Padrão de proveniência |
| IaC Impact | Nenhum (SQLite local) | Path configurável em `config/serving.yaml` |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Escopo de endpoints? | **(c) Tudo no serving** + erros 4xx/5xx | Middleware global `/api/*` |
| 2 | Uso principal? | **(d) Debug + auditoria + analytics** | Schema rico; fase 2 views SQL |
| 3 | Persistência? | **(d) SQLite SSOT permanente** | Sem migração Postgres; SQL como produto |
| 4 | Amostras? | **(d)+(b)** schemas Pydantic + fixtures | Schema derivado de `serving/schemas.py` |

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input fixtures | `tests/serving/test_*.py` | ~6 | Payload JSON completos |
| Ground truth rows | `base/primeira_base.csv` | 1902 | Referência de variáveis |
| Schemas | `src/serving/schemas.py` | 1 | Contrato request/response |
| JSONL precedente | `logs/simulation/*.jsonl` | 2+ | Padrão evento, não HTTP |

---

## Approaches Explored

### Approach A: Middleware + SQLite SSOT ⭐ Recommended

Middleware FastAPI captura request/response/erro; INSERT síncrono em `api_calls` (WAL).

**Pros:** SSOT único; SQL para debug/audit/analytics; alinhado à decisão permanente.  
**Cons:** Latência +1–5 ms; multipart precisa resumo (hash, não blob).

### Approach B: JSONL + SQLite índice

Dual-write como simulation logs.

**Cons:** Duas fontes; rejeitado para SSOT.

### Approach C: OpenTelemetry

**Cons:** Infra extra; não atende SQLite permanente.

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A |
| **User Confirmation** | 2026-07-13 (via `/define` sem objeção) |
| **Reasoning** | SSOT, escopo total, zero infra adicional |

---

## Features Removed (YAGNI)

| Feature | Reason | Later? |
|---------|--------|--------|
| Dashboard web | SQL direto basta | Sim |
| CSV blob completo (simulate) | hash + metadados MVP | Sim |
| Migração Postgres | Decisão SSOT | Não |
| TTL automático | SSOT permanente | Backup manual |
| Auth multi-tenant | MVP local | Sim |

---

## Suggested Requirements for /define

Ver `DEFINE_SERVING_SQLITE_AUDIT.md`.

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_SERVING_SQLITE_AUDIT.md`

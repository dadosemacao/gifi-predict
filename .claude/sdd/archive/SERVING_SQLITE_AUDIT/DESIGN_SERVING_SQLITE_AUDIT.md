# DESIGN: Serving SQLite Audit

> Middleware ASGI + repositório SQLite para auditoria call-by-call do GIFI Serving

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | SERVING_SQLITE_AUDIT |
| **Date** | 2026-07-13 |
| **Author** | Emerson Antônio |
| **DEFINE** | [DEFINE_SERVING_SQLITE_AUDIT.md](./DEFINE_SERVING_SQLITE_AUDIT.md) |
| **Status** | ✅ Shipped |

---

## Architecture Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         GIFI Serving (FastAPI)                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Client (Postman / UI / curl)                                             │
│       │                                                                   │
│       ▼                                                                   │
│  ┌─────────────────┐                                                      │
│  │ AuditMiddleware │  ← intercepta apenas path.startswith("/api/")       │
│  │  (ASGI pure)    │                                                      │
│  └────────┬────────┘                                                      │
│           │ cache request body │ wrap send() │ measure duration           │
│           ▼                                                               │
│  ┌─────────────────┐     ┌──────────────────┐                            │
│  │  API Routers    │────▶│ resolve_process  │ (forecast / predict-tsa)   │
│  │ forecast        │     │ field_origins    │                            │
│  │ predict-tsa     │     └──────────────────┘                            │
│  │ simulate        │                                                      │
│  │ release-status  │                                                      │
│  └────────┬────────┘                                                      │
│           │ response JSON / HTTPException                                  │
│           ▼                                                               │
│  ┌─────────────────┐     ┌──────────────────┐                            │
│  │ ResponseParser  │────▶│ AuditRepository  │                            │
│  │ (extractors)    │     │  sqlite3 + WAL   │                            │
│  └─────────────────┘     └────────┬─────────┘                            │
│                                 │ INSERT api_calls                        │
│                                 ▼                                         │
│                        logs/serving_audit.db  (SSOT)                      │
│                                 │                                         │
│                                 ▼                                         │
│                        scripts/audit_query.py  (CLI SQL)                  │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `AuditMiddleware` | Captura request/response, duração, erros | ASGI middleware (Starlette-compatible) |
| `RequestCapture` | Buffer body JSON ou resumo multipart + SHA-256 | `hashlib`, `multipart` parsing leve |
| `ResponseExtractor` | Extrai `field_origins`, `metrics`, `model_id` do JSON de saída | `json.loads` defensivo |
| `AuditRepository` | INSERT síncrono, pragmas WAL | `sqlite3` stdlib |
| `migrate.py` | Aplica `001_init.sql` idempotente | SQL versionado |
| `audit_query.py` | Consultas operacionais (--last, --errors) | CLI argparse |

---

## Key Decisions

### Decision 1: ASGI Middleware puro (não BaseHTTPMiddleware)

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** Precisamos capturar body de request e response sem quebrar streaming ou multipart.

**Choice:** Implementar middleware ASGI de baixo nível com wrappers `receive` / `send`.

**Rationale:** `BaseHTTPMiddleware` bufferiza de forma problemática com uploads grandes; ASGI puro permite ler body uma vez, re-injetar para downstream, e acumular chunks de response.

**Alternatives Rejected:**
1. Decorator por rota — rejeitado: não cobre 100% `/api/*` nem erros globais de validação
2. JSONL append-only — rejeitado: contradiz SSOT SQLite permanente

**Consequences:**
- Mais código boilerplate ASGI
- Controle total sobre simulate multipart (hash incremental)

---

### Decision 2: Escrita síncrona antes de fechar response

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** Auditoria exige registro antes do client receber resposta (DEFINE freshness SLA).

**Choice:** `repository.insert(record)` síncrono no final do middleware, antes do último chunk enviado ao client (após acumular response).

**Rationale:** Garante row persistida quando response completa; SQLite WAL com single writer é adequado para MVP.

**Alternatives Rejected:**
1. Background task / queue — risco de perda se processo morrer
2. Async aiosqlite — complexidade extra sem ganho no volume MVP

**Consequences:**
- +1–10 ms latência por call (aceitável per DEFINE)
- Falha no INSERT não deve derrubar API (log + continuar)

---

### Decision 3: Multipart simulate — hash + metadados, sem blob

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** CSV de cenário pode ser grande; SSOT deve ser consultável.

**Choice:** No middleware, detectar `Content-Type: multipart/form-data` em `/api/simulate` e `/api/scenario/validate`:
- Calcular `file_sha256` enquanto stream passa ao handler (body re-injetado)
- `request_json` = `{"mode","demo","run_id","file_name","file_sha256","content_type":"multipart"}`

**Rationale:** Atende AT-004; permite correlacionar upload sem inflar DB.

**Alternatives Rejected:**
1. Armazenar CSV inteiro — rejeitado YAGNI
2. Salvar cópia em disco separada — duplicação de SSOT

---

### Decision 4: Filtro `/api/*` only

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Context:** `StaticFiles` montado em `/` serviria assets SPA.

**Choice:** Auditar somente paths onde `scope["path"].startswith("/api/")`.

**Rationale:** Escopo DEFINE; evita poluir DB com GET de `.js`/`.css`.

---

### Decision 5: Endpoint normalizado via mapa fixo

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-07-13 |

**Choice:**

| Path | `endpoint` |
|------|------------|
| `POST /api/forecast` | `forecast` |
| `GET /api/forecast/status` | `forecast_status` |
| `POST /api/predict-tsa` | `predict_tsa` |
| `GET /api/predict-tsa/status` | `predict_tsa_status` |
| `POST /api/simulate` | `simulate` |
| `POST /api/scenario/validate` | `scenario_validate` |
| `GET /api/release-status` | `release_status` |
| `GET /api/template` | `template` |
| outros `/api/*` | slug do path (`api_unknown`) |

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `database/serving_audit/001_init.sql` | Create | Schema `api_calls` + índices + `schema_migrations` | @python-developer | None |
| 2 | `src/serving/observability/__init__.py` | Create | Package export | @python-developer | None |
| 3 | `src/serving/observability/schema.py` | Create | `ApiCallRecord` dataclass | @python-developer | None |
| 4 | `src/serving/observability/extractors.py` | Create | Parse response, normalize endpoint, multipart summary | @python-developer | 3 |
| 5 | `src/serving/observability/repository.py` | Create | SQLite INSERT + connection factory | @python-developer | 1, 3 |
| 6 | `src/serving/observability/migrate.py` | Create | Run migrations on startup | @python-developer | 1, 5 |
| 7 | `src/serving/observability/middleware.py` | Create | ASGI audit middleware | @python-developer | 4, 5 |
| 8 | `src/serving/config.py` | Modify | `audit_enabled`, `audit_db_path` | @python-developer | None |
| 9 | `config/serving.yaml` | Modify | Defaults audit | @python-developer | 8 |
| 10 | `src/serving/app.py` | Modify | Register middleware + migrate on startup | @python-developer | 6, 7 |
| 11 | `scripts/audit_query.py` | Create | CLI consultas | @shell-script-specialist | 5 |
| 12 | `tests/serving/test_audit_repository.py` | Create | Unit INSERT/SELECT | @test-generator | 5 |
| 13 | `tests/serving/test_audit_middleware.py` | Create | Integration AT-001..005 | @test-generator | 7, 10 |
| 14 | `tests/serving/conftest.py` | Modify | Fixture `audit_db` tmp_path | @test-generator | 8 |
| 15 | `docs/CHANGELOG.md` | Modify | Entrada feature audit | @code-documenter | Build |

**Total Files:** 15 (11 create, 4 modify)

---

## Agent Assignment Rationale

| Agent | Files | Why |
|-------|-------|-----|
| @python-developer | 1–10 | Middleware ASGI, sqlite3, integração FastAPI |
| @shell-script-specialist | 11 | CLI `audit_query.py` |
| @test-generator | 12–14 | AT-001..007 cobertura pytest |
| @code-documenter | 15 | CHANGELOG pós-build |

---

## Code Patterns

### Pattern 1: ApiCallRecord

```python
# src/serving/observability/schema.py
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, UTC

@dataclass
class ApiCallRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    ts_utc: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    method: str = ""
    path: str = ""
    endpoint: str = ""
    status_code: int = 0
    duration_ms: float = 0.0
    client_ip: str | None = None
    user_agent: str | None = None
    product: str | None = None
    model_id: str | None = None
    family: str | None = None
    run_id: str | None = None
    request_json: str | None = None
    response_json: str | None = None
    field_origins_json: str | None = None
    warnings_json: str | None = None
    metrics_json: str | None = None
    file_sha256: str | None = None
    file_name: str | None = None
    row_count: int | None = None
    mode: str | None = None
    error_detail: str | None = None
```

### Pattern 2: Response field extraction

```python
# src/serving/observability/extractors.py
import json

def enrich_from_response(record: ApiCallRecord, body: bytes, status: int) -> None:
    if not body:
        return
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        record.response_json = body.decode("utf-8", errors="replace")[:65536]
        return
    record.response_json = json.dumps(data, ensure_ascii=False)
    if status >= 400:
        record.error_detail = str(data.get("detail", ""))
        return
    record.product = data.get("product")
    record.model_id = data.get("model_id")
    record.family = data.get("family")
    if fo := data.get("field_origins"):
        record.field_origins_json = json.dumps(fo, ensure_ascii=False)
    if w := data.get("warnings"):
        record.warnings_json = json.dumps(w, ensure_ascii=False)
    if m := data.get("metrics"):
        record.metrics_json = json.dumps(m, ensure_ascii=False)
    # simulate extras
    record.row_count = data.get("row_count") or record.row_count
    record.mode = data.get("mode") or record.mode
```

### Pattern 3: Repository INSERT (WAL)

```python
# src/serving/observability/repository.py
import sqlite3
from pathlib import Path

class AuditRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def insert(self, record: ApiCallRecord) -> None:
        cols = [f.name for f in dataclasses.fields(record)]
        placeholders = ",".join("?" * len(cols))
        sql = f"INSERT INTO api_calls ({','.join(cols)}) VALUES ({placeholders})"
        with self._connect() as conn:
            conn.execute(sql, tuple(getattr(record, c) for c in cols))
            conn.commit()
```

### Pattern 4: Middleware skeleton

```python
# src/serving/observability/middleware.py
import time
from starlette.types import ASGIApp, Receive, Scope, Send

class AuditMiddleware:
    def __init__(self, app: ASGIApp, repository: AuditRepository, enabled: bool = True):
        self.app = app
        self.repository = repository
        self.enabled = enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return
        if not self.enabled:
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        request_body = bytearray()
        more_body = True

        async def receive_wrapper() -> dict:
            nonlocal more_body
            message = await receive()
            if message["type"] == "http.request":
                request_body.extend(message.get("body", b""))
                more_body = message.get("more_body", False)
            return message

        status_code = 500
        response_body = bytearray()

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        finally:
            record = build_record(scope, bytes(request_body), bytes(response_body),
                                  status_code, (time.perf_counter() - started) * 1000)
            try:
                self.repository.insert(record)
            except Exception:
                logger.exception("audit_insert_failed", extra={"path": scope["path"]})
```

### Pattern 5: Config

```yaml
# config/serving.yaml (append)
audit_enabled: true
audit_db_path: "logs/serving_audit.db"
```

### Pattern 6: SQL migration

```sql
-- database/serving_audit/001_init.sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_calls (
    id TEXT PRIMARY KEY,
    ts_utc TEXT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    client_ip TEXT,
    user_agent TEXT,
    product TEXT,
    model_id TEXT,
    family TEXT,
    run_id TEXT,
    request_json TEXT,
    response_json TEXT,
    field_origins_json TEXT,
    warnings_json TEXT,
    metrics_json TEXT,
    file_sha256 TEXT,
    file_name TEXT,
    row_count INTEGER,
    mode TEXT,
    error_detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_calls_ts ON api_calls(ts_utc);
CREATE INDEX IF NOT EXISTS idx_api_calls_endpoint ON api_calls(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_calls_status ON api_calls(status_code);
CREATE INDEX IF NOT EXISTS idx_api_calls_product ON api_calls(product);
```

---

## Data Flow

```text
1. HTTP request chega em /api/forecast
   │
   ▼
2. AuditMiddleware: buffer request body (JSON)
   │
   ▼
3. FastAPI route → resolve_process_fields → predict → JSON response
   │
   ▼
4. Middleware acumula response body via send_wrapper
   │
   ▼
5. ResponseExtractor preenche ApiCallRecord (metrics, field_origins, …)
   │
   ▼
6. AuditRepository.insert() — commit SQLite
   │
   ▼
7. Client recebe HTTP response (body já enviado durante send_wrapper)
```

**Nota implementação:** INSERT ocorre após response completa enviada ao client (trade-off: SLA de persistência = "antes de encerrar conexão", não antes do primeiro byte). Se stakeholder exigir insert-before-bytes, mover INSERT para antes do último `send(body)` — documentado como risco AT-001.

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|------------------|----------------|
| SQLite file | Local filesystem | N/A |
| FastAPI routers | In-process | N/A |
| `logs/` directory | Write | Repo-relative path |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Repository INSERT/SELECT, extractors | `test_audit_repository.py` | pytest + tmp_path SQLite | 100% repository |
| Integration | Middleware + app (AT-001..005) | `test_audit_middleware.py` | pytest, TestClient* | Happy + 422 paths |
| CLI | audit_query --last | manual / subprocess | pytest optional | AT-007 |
| Load smoke | 100 sequential inserts | `test_audit_middleware.py` | pytest | Zero loss (DEFINE) |

\* TestClient requer `httpx` no ambiente; testes de repository + middleware unitário não dependem dele.

| AT ID | Test mapping |
|-------|--------------|
| AT-001 | `test_audit_forecast_persists_row` |
| AT-002 | `test_audit_predict_tsa_proxy_origins` |
| AT-003 | `test_audit_validation_error_422` |
| AT-004 | `test_audit_simulate_multipart_hash` |
| AT-005 | `test_audit_status_get` |
| AT-006 | `test_migrations_idempotent` |
| AT-007 | `test_audit_query_cli_last_n` |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| SQLite locked / busy | Log `audit_insert_failed`; não falhar request | No |
| JSON parse response | Salvar raw truncado 64KB | No |
| Multipart parse fail | `request_json={"parse_error": true}` | No |
| Disk full | Log exception; API continua | No |
| `audit_enabled=false` | Middleware pass-through | N/A |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `audit_enabled` | bool | `true` | Liga/desliga middleware |
| `audit_db_path` | string | `logs/serving_audit.db` | Caminho SSOT SQLite |
| `audit_max_body_bytes` | int | `65536` | Truncar JSON bruto acima deste tamanho |

Env override: `GIFI_SERVING_AUDIT_ENABLED`, `GIFI_SERVING_AUDIT_DB_PATH`

---

## Security Considerations

- DB local contém variáveis de processo — não expor via rota pública (Fase 2 read API exige auth)
- `logs/serving_audit.db` deve estar no `.gitignore` se não estiver
- Truncar bodies evita DoS por payload gigante
- Sem PII identificada; revisar se campos futuros exigirem mascaramento

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | `logger.exception` em falha de INSERT; evento `audit_insert_failed` |
| Metrics | Fase 2: view SQL `v_daily_volume` |
| Tracing | Fora de escopo (DEFINE) |
| SSOT | `logs/serving_audit.db` consultável via `scripts/audit_query.py` |

---

## Fase 2 (documentado, não build MVP)

- `GET /api/audit/calls?limit=50&endpoint=forecast`
- Views: `v_daily_volume`, `v_proxy_rate`, `v_error_rate`
- Correlação `X-Request-ID` header opcional

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1 | 2026-07-13 | Emerson Antônio | Shipped and archived |

---

## Next Step

**Ready for:** `/build .claude/sdd/features/DESIGN_SERVING_SQLITE_AUDIT.md`

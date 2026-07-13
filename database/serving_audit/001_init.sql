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

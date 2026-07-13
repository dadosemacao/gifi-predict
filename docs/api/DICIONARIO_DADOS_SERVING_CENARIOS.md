# Dicionário de Dados — APIs de Cenários e Metadados

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.0  
**Escopo:** `POST /api/scenario/validate`, `POST /api/simulate`, `GET /api/release-status`, `GET /api/template`  
**Fonte de verdade (código):** `src/serving/schemas.py`, `src/serving/routes/scenario.py`, `src/serving/routes/release.py`, `src/serving/routes/static.py`

---

## 1. Visão geral

| Endpoint | Método | Produto | Objetivo |
|----------|--------|---------|----------|
| `/api/scenario/validate` | POST | Validação online | Checagem leve de schema/mix antes da inferência |
| `/api/simulate` | POST | Cenário cascata | Upload planilha → curvas TSA/Carga/Extrativo + top-3 detratores |
| `/api/release-status` | GET | Metadados L4 | Status do gate A∧B∧C e campeões |
| `/api/template` | GET | Template v0 | Download CSV de exemplo para upload |

Inferência JSON (forecast / predict-tsa): ver [DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md](DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md).

---

## 2. POST /api/scenario/validate

Validação **síncrona e leve** do upload — sem inferência cascata.

### 2.1 Request

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `file` | file | Sim | `.xlsx` ou `.csv` conforme template v0 |
| `mode` | string | Não (default `A`) | `"A"` ou `"B"` — Modo A/B do domínio |

### 2.2 Response (`ValidateResponse`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ok` | boolean | `true` se validação passou |
| `row_count` | integer \| null | Linhas parseadas |
| `sla_ms` | integer \| null | Tempo de validação (ms) |
| `signal` | string \| null | Sinal `INGEST_*` principal, se houver |
| `errors` | string[] | Mensagens de erro (vazio se `ok=true`) |

### 2.3 Exemplo

```bash
curl -X POST http://127.0.0.1:8000/api/scenario/validate \
  -F "file=@cenario.csv" \
  -F "mode=A"
```

```json
{
  "ok": true,
  "row_count": 12,
  "sla_ms": 45,
  "signal": null,
  "errors": []
}
```

---

## 3. POST /api/simulate

Inferência **cascata Elo 1→2→3** sobre planilha de cenário.

### 3.1 Request

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| `file` | file | Sim | — | Planilha cenário (.xlsx / .csv) |
| `mode` | string | Não | `"A"` | Modo A (cascata completa) ou B (injeta Extrativo) |
| `demo` | boolean | Não | `true` | `false` exige `release_ok=true` (L4) |
| `run_id` | string | Não | config default | Override do candidato L3/L4 |

### 3.2 Política de release

| `demo` | `release_ok` | HTTP |
|--------|--------------|------|
| `true` | qualquer | 200 |
| `false` | `true` | 200 |
| `false` | `false` | **403** |

> UI (2026-07-13): o upload de cenário respeita `release_ok`. Com `release_ok=false`
> o toggle "Modo demonstração" fica travado (`demo=true`); com `release_ok=true`
> o usuário pode enviar `demo=false`. Ver [GAPS_UI_E_VALIDACAO.md](GAPS_UI_E_VALIDACAO.md).

### 3.3 Response (`InferenceResponse`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `mode` | `"A"` \| `"B"` | Modo executado |
| `demo` | boolean | Flag demo da request |
| `gate_ok` | boolean | Alias de `release_ok` do contexto L4 |
| `model_id` | string | Identificador do run/candidato |
| `acceptance_run_id` | string | Run do relatório de aceite |
| `l2_dataset_version` | string | Versão L2 usada |
| `curves` | `CurvePoint[]` | Série temporal por linha/dia do cenário |
| `detractors` | `DetractorOut[]` | Top-3 detratores (max 3) |
| `warnings` | string[] | Alertas de ingest/proxy/imputação |
| `metrics` | object | Métricas auxiliares (MAE holdout, etc.) |

#### `CurvePoint`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `label` | string | Identificador da linha (ex.: data ou índice) |
| `tsa_dia` | float | TSA predita (t/dia) |
| `carga_alcalina` | float | Carga predita ou injetada |
| `extrativo_at` | float | Extrativo predito ou injetado |

#### `DetractorOut`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `feature` | string | Nome da feature |
| `delta_tsa` | float | Contribuição em ΔTSA |
| `method` | `"shap"` \| `"coef"` \| `"permutation"` | Método de explicabilidade |

### 3.4 Exemplo

```bash
curl -X POST http://127.0.0.1:8000/api/simulate \
  -F "file=@cenario.csv" \
  -F "mode=A" \
  -F "demo=true"
```

```json
{
  "mode": "A",
  "demo": true,
  "gate_ok": false,
  "model_id": "2026-07-10T10:54:42.849161Z",
  "acceptance_run_id": "2026-07-10T10:54:42.849161Z",
  "l2_dataset_version": "excel_validation",
  "curves": [
    {
      "label": "C-DEMO",
      "tsa_dia": 3420.5,
      "carga_alcalina": 19.2,
      "extrativo_at": 1.85
    }
  ],
  "detractors": [
    { "feature": "DB_SGF", "delta_tsa": -42.1, "method": "shap" }
  ],
  "warnings": [],
  "metrics": { "mae_tsa_holdout": 96.7 }
}
```

---

## 4. GET /api/release-status

Consulta o contexto de release L4 (gate A∧B∧C).

### 4.1 Query params

| Param | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `run_id` | string | Não | Override; default em `config/serving.yaml` |

### 4.2 Response (`ReleaseStatusResponse`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `run_id` | string | Run do candidato/aceite |
| `release_ok` | boolean | `true` somente se A∧B∧C verdes |
| `demo_mode` | boolean | `true` quando release bloqueado |
| `l2_dataset_version` | string | Versão L2 associada |
| `mae_tsa_holdout` | float \| null | MAE TSA no holdout |
| `champions` | object | Mapa elo → família campeã |
| `matriz_a_ok` | boolean \| null | Resultado Matriz A |
| `matriz_b_ok` | boolean \| null | Resultado Matriz B |
| `matriz_c_ok` | boolean \| null | Resultado Matriz C |

### 4.3 Exemplo

```bash
curl http://127.0.0.1:8000/api/release-status
```

```json
{
  "run_id": "2026-07-10T10:54:42.849161Z",
  "release_ok": false,
  "demo_mode": true,
  "l2_dataset_version": "excel_validation",
  "mae_tsa_holdout": 96.7,
  "champions": { "elo1": "randomforest", "elo2": "randomforest", "elo3": "catboost" },
  "matriz_a_ok": false,
  "matriz_b_ok": false,
  "matriz_c_ok": true
}
```

---

## 5. GET /api/template

Retorna CSV de exemplo baseado em `docs/kb/gifi-domain/specs/template_cenario_v0.yaml`.

### 5.1 Response

**Content-Type:** `text/csv`  
**Content-Disposition:** `attachment; filename="template_cenario_v0.csv"`

Linha de cabeçalho + uma linha demo conforme `example_header_csv` do YAML.

### 5.2 Erros

| HTTP | `detail` | Causa |
|------|----------|-------|
| 404 | `template_not_found` | Arquivo YAML ausente |
| 404 | `template_csv_not_defined` | `example_header_csv` vazio |

---

## 6. Códigos HTTP

| Código | Endpoints | Causa típica |
|--------|-----------|--------------|
| 200 | Todos | Sucesso |
| 400 | validate, simulate | Formato de arquivo inválido |
| 403 | simulate | `demo=false` com `release_ok=false` |
| 404 | template | Template não configurado |
| 422 | — | N/A nestes endpoints (validação retorna `ok=false`) |
| 500 | simulate | Falha na inferência ou I/O |

---

## 7. Auditoria

Chamadas registradas em `logs/serving_audit.db` quando `audit_enabled: true`.

Campos capturados: método, path, status, duração, corpo (truncado), hash de upload multipart.

Consulta: `python scripts/audit_query.py --last 10`

---

## 8. Configuração (`config/serving.yaml`)

| Chave | Default | Descrição |
|-------|---------|-----------|
| `host` | `127.0.0.1` | Bind host |
| `port` | `8000` | Bind port |
| `default_run_id` | — | Run cascata default |
| `demo_default` | `true` | Default demo na UI |
| `ephemeral_prefix` | `ui-` | Prefixo de cenários efêmeros online |
| `template_path` | template v0 YAML | Fonte do `/api/template` |
| `audit_enabled` | `true` | Middleware de auditoria |
| `audit_db_path` | `logs/serving_audit.db` | SQLite audit |
| `audit_max_body_bytes` | `65536` | Truncamento de corpo |

---

## 9. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [README.md](README.md) | Índice geral das APIs |
| [DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md](DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md) | Forecast + predict-tsa |
| [../kb/gifi-domain/specs/template_cenario_v0.yaml](../kb/gifi-domain/specs/template_cenario_v0.yaml) | Contrato colunas cenário |
| [../kb/gifi-domain/concepts/mode-a-b.md](../kb/gifi-domain/concepts/mode-a-b.md) | Modo A/B normativo |

---

*Atualizar ao alterar schemas Pydantic ou política de release.*

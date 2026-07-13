# Documentação das APIs REST — GIFI Serving

**Autor:** Emerson Antônio  
**Data:** 2026-07-13  
**Versão:** 1.0  
**Base URL (local):** `http://127.0.0.1:8000`

---

## 1. Visão geral

O pacote `src/serving/` expõe a **Camada 5** do GIFI via FastAPI. Três famílias de endpoints:

| Família | Endpoints | Produto | Documento |
|---------|-----------|---------|-----------|
| **Cenários cascata** | `/api/scenario/*`, `/api/simulate` | Upload planilha → curvas Modo A/B + detratores | [DICIONARIO_DADOS_SERVING_CENARIOS.md](DICIONARIO_DADOS_SERVING_CENARIOS.md) |
| **Forecast + What-if** | `/api/forecast`, `/api/predict-tsa` | Inferência JSON com 13 preditores | [DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md](DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md) |
| **Metadados** | `/api/release-status`, `/api/template` | Gate L4 + template cenário v0 | [DICIONARIO_DADOS_SERVING_CENARIOS.md](DICIONARIO_DADOS_SERVING_CENARIOS.md) |

**Fonte de verdade (código):**

- Schemas: `src/serving/schemas.py`
- Rotas: `src/serving/routes/`
- Serviços: `src/serving/services/`
- Política release: `src/serving/policy/release.py`
- Config: `config/serving.yaml`

---

## 2. Catálogo rápido

| Método | Path | Content-Type | Descrição |
|--------|------|--------------|-----------|
| POST | `/api/scenario/validate` | `multipart/form-data` | Validação leve de upload |
| POST | `/api/simulate` | `multipart/form-data` | Inferência cascata + curvas + top-3 |
| POST | `/api/forecast` | `application/json` | Forecast operacional (requer `tsa_history`) |
| GET | `/api/forecast/status` | — | Status do modelo forecast |
| POST | `/api/predict-tsa` | `application/json` | What-if direto (Lasso, 13 preditores) |
| GET | `/api/predict-tsa/status` | — | Status do modelo what-if |
| GET | `/api/release-status` | — | `release_ok`, `demo_mode`, MAE holdout |
| GET | `/api/template` | — | YAML template cenário v0 |

---

## 3. Política de release (L4)

| `demo` (request) | `release_ok` (L4) | Resultado |
|------------------|-------------------|-----------|
| `true` | qualquer | **200** — modo demonstração |
| `false` | `true` | **200** — bind produtivo |
| `false` | `false` | **403** — bloqueado |

Default: `demo_default: true` em `config/serving.yaml`.

---

## 4. Auditoria

Todos os endpoints `/api/*` são registrados em SQLite quando `audit_enabled: true`.

| Item | Valor |
|------|-------|
| Banco | `logs/serving_audit.db` |
| Migração | `database/serving_audit/001_init.sql` |
| CLI | `python scripts/audit_query.py --last N` |
| Limite corpo | `audit_max_body_bytes: 65536` |

---

## 5. Códigos HTTP comuns

| Código | Contexto |
|--------|----------|
| 200 | Sucesso |
| 400 | Arquivo não suportado / parse inválido |
| 403 | `demo=false` sem `release_ok` |
| 422 | Campos fora das faixas oficiais ou ausentes |
| 404 | Artefato de modelo não encontrado |
| 500 | Erro interno (inferência, I/O) |

---

## 6. Desenvolvimento

```bash
serve run --port 8000          # produção local (SPA + API)
./scripts/dev_ui.sh            # dev: Vite :5173 + API :8000
pytest tests/serving/ -q       # testes AT serving
```

OpenAPI interativo: `http://127.0.0.1:8000/docs` (Swagger UI automático FastAPI).

---

## 7. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md](DICIONARIO_DADOS_FORECAST_PREDICT_TSA.md) | Contrato completo forecast + predict-tsa |
| [DICIONARIO_DADOS_SERVING_CENARIOS.md](DICIONARIO_DADOS_SERVING_CENARIOS.md) | Contrato simulate + validate + release |
| [../guides/DEV_ENVIRONMENT.md](../guides/DEV_ENVIRONMENT.md) | Setup e comandos |
| [../kb/ml-tabular/patterns/inference-serving.md](../kb/ml-tabular/patterns/inference-serving.md) | Padrão KB Camada 5 |

---

*Atualizar este índice ao adicionar novos endpoints ou produtos de inferência.*

# Débitos de Segurança — Serving (Camada 5)

**Autor:** Emerson Antônio
**Data:** 2026-07-13
**Versão:** 1.0
**Status:** Registro de débito — nenhuma correção implementada nesta onda.

---

## 1. Contexto

A revisão de código de 2026-07-13 identificou riscos de segurança no serving
FastAPI (`src/serving/`). Esta onda priorizou produto/UX; os itens abaixo ficam
**documentados como débito** e não foram corrigidos. Premissa atual de operação:
**rede interna confiável / localhost** (`host: 127.0.0.1` em `config/serving.yaml`).

> Aviso: não expor a API fora da rede interna até endereçar os itens Critical e High.

---

## 2. Débitos priorizados

| # | Severidade | Item | Local | Risco |
|---|-----------|------|-------|-------|
| 1 | Critical | Ausência de autenticação / autorização / rate limiting | `src/serving/app.py` | Qualquer cliente na rede aciona inferência e leitura de status |
| 2 | Critical | `joblib.load` sem contenção de path nem verificação de assinatura | `policy/tsa_loader.py`, `forecast/predictor.py`, `policy/extr_imputer_loader.py` | Desserialização insegura (pickle) se path for manipulável |
| 3 | High | Path traversal via `run_id` interpolado em paths | `policy/release.py`, `policy/forecast_loader.py`, `policy/tsa_loader.py` | Leitura fora de `reports/` e `models/` |
| 4 | High | Upload e corpo HTTP lidos sem limite de tamanho | `routes/scenario.py`, `services/validate.py`, `observability/middleware.py` | DoS por memória |
| 5 | High | Handlers `async` executando pipeline síncrono pesado | `routes/scenario.py` | Bloqueio do event loop sob concorrência |

---

## 3. Ordem de remediação sugerida (próxima onda)

1. **Sanitizar `run_id`** — regex `^[A-Za-z0-9._:-]+$` + `resolved.is_relative_to(base)` em todos os loaders.
2. **Unificar loader seguro** — reutilizar o padrão de `simulation/package/publisher.py::load_pipeline` (`is_relative_to(models_root)`) em `tsa_loader`, `forecast/predictor` e `extr_imputer_loader`.
3. **Limite de upload/corpo** — impor `max_upload_bytes` (ex.: 10 MB) e cap no `AuditMiddleware`; retornar 413.
4. **Autenticação mínima** — API key via header/middleware ou reverse proxy; rate limit básico.
5. **Descarregar trabalho pesado** — `run_in_executor` ou endpoints síncronos + workers Uvicorn.

---

## 4. Referência

Padrão seguro já existente (usar como base):

```17:22:src/simulation/package/publisher.py
def load_pipeline(path: Path, models_root: Path) -> Pipeline:
    resolved = path.resolve()
    root = models_root.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"joblib path outside models_root: {resolved}")
    return joblib.load(resolved)
```

---

## 5. Relacionados

- [../api/GAPS_UI_E_VALIDACAO.md](../api/GAPS_UI_E_VALIDACAO.md)
- [../api/README.md](../api/README.md)
- [DEV_ENVIRONMENT.md](DEV_ENVIRONMENT.md) — débitos Marco 2–3
